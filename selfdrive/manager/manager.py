#!/usr/bin/env python3
import datetime
import os
import signal
import sys
import traceback
from typing import List, Tuple, Union

from cereal import log
import cereal.messaging as messaging
import openpilot.selfdrive.sentry as sentry
from openpilot.common.basedir import BASEDIR
from openpilot.common.params import Params, ParamKeyType
from openpilot.common.text_window import TextWindow
from openpilot.selfdrive.boardd.set_time import set_time
from openpilot.system.hardware import HARDWARE, PC
from openpilot.selfdrive.manager.helpers import unblock_stdout, write_onroad_params, save_bootlog
from openpilot.selfdrive.manager.process import ensure_running
from openpilot.selfdrive.manager.process_config import managed_processes
from openpilot.selfdrive.athena.registration import register, UNREGISTERED_DONGLE_ID
from openpilot.common.swaglog import cloudlog, add_file_handler
from openpilot.system.version import is_dirty, get_commit, get_version, get_origin, get_short_branch, \
                           get_normalized_origin, terms_version, training_version, \
                           is_tested_branch, is_release_branch

from openpilot.selfdrive.frogpilot.functions.model_switcher import set_model

PREBUILT_FILE = os.path.join(BASEDIR, 'prebuilt')

def manager_init() -> None:
  # update system time from panda
  set_time(cloudlog)

  # save boot log
  save_bootlog()

  # Clear the error log on boot to prevent old errors from hanging around
  if os.path.isfile(os.path.join(sentry.CRASHES_DIR, 'error.txt')):
    os.remove(os.path.join(sentry.CRASHES_DIR, 'error.txt'))

  params = Params()
  params.clear_all(ParamKeyType.CLEAR_ON_MANAGER_START)
  params.clear_all(ParamKeyType.CLEAR_ON_ONROAD_TRANSITION)
  params.clear_all(ParamKeyType.CLEAR_ON_OFFROAD_TRANSITION)
  if is_release_branch():
    params.clear_all(ParamKeyType.DEVELOPMENT_ONLY)

  FrogsGoMoo = get_short_branch() == "FrogPilot-Development"

  default_params: List[Tuple[str, Union[str, bytes]]] = [
    ("CompletedTrainingVersion", "0.2.0" if FrogsGoMoo else "0"),
    ("DisengageOnAccelerator", "0"),
    ("GsmMetered", "0" if FrogsGoMoo else "1"),
    ("HasAcceptedTerms", "2" if FrogsGoMoo else "0"),
    ("LanguageSetting", "main_en"),
    ("OpenpilotEnabledToggle", "1"),
    ("LongitudinalPersonality", str(log.LongitudinalPersonality.standard)),

    # Default FrogPilot parameters
    ("AccelerationPath", "1"),
    ("AccelerationProfile", "3" if FrogsGoMoo else "2"),
    ("AdjacentPath", "1" if FrogsGoMoo else "0"),
    ("AdjacentPathMetrics", "1" if FrogsGoMoo else "0"),
    ("AdjustablePersonalities", "1"),
    ("AggressiveAcceleration", "1"),
    ("AggressiveFollow", "10" if FrogsGoMoo else "12"),
    ("AggressiveJerk", "6" if FrogsGoMoo else "5"),
    ("AlwaysOnLateral", "1"),
    ("AlwaysOnLateralMain", "1" if FrogsGoMoo else "0"),
    ("BlindSpotPath", "1"),
    ("CameraView", "1" if FrogsGoMoo else "0"),
    ("CECurves", "1"),
    ("CENavigation", "1"),
    ("CESignal", "1"),
    ("CESlowerLead", "0"),
    ("CESpeed", "0"),
    ("CESpeedLead", "0"),
    ("CEStopLights", "1"),
    ("CEStopLightsLead", "0" if FrogsGoMoo else "1"),
    ("Compass", "1" if FrogsGoMoo else "0"),
    ("ConditionalExperimental", "1"),
    ("CurveSensitivity", "125" if FrogsGoMoo else "100"),
    ("CustomColors", "1"),
    ("CustomIcons", "1"),
    ("CustomPersonalities", "1"),
    ("CustomSignals", "1"),
    ("CustomSounds", "1"),
    ("CustomTheme", "1"),
    ("CustomUI", "1"),
    ("DeviceShutdown", "9"),
    ("DriverCamera", "0"),
    ("DriveStats", "1"),
    ("EVTable", "0" if FrogsGoMoo else "1"),
    ("ExperimentalModeActivation", "1"),
    ("ExperimentalModeViaLKAS", "1" if FrogsGoMoo else "0"),
    ("ExperimentalModeViaScreen", "0" if FrogsGoMoo else "1"),
    ("Fahrenheit", "0"),
    ("FireTheBabysitter", "1" if FrogsGoMoo else "0"),
    ("FPSCounter", "1" if FrogsGoMoo else "0"),
    ("FullMap", "0"),
    ("GasRegenCmd", "0"),
    ("GoatScream", "1"),
    ("GreenLightAlert", "0"),
    ("HideSpeed", "0"),
    ("HideSpeedUI", "0"),
    ("HigherBitrate", "1" if FrogsGoMoo else "0"),
    ("LaneChangeTime", "0"),
    ("LaneDetection", "1"),
    ("LaneLinesWidth", "4"),
    ("LateralTune", "1"),
    ("LeadInfo", "1" if FrogsGoMoo else "0"),
    ("LockDoors", "0"),
    ("LongitudinalTune", "1"),
    ("LongPitch", "0" if FrogsGoMoo else "1"),
    ("LowerVolt", "0" if FrogsGoMoo else "1"),
    ("MTSCAggressiveness", "100" if FrogsGoMoo else "100"),
    ("Model", "0"),
    ("ModelUI", "1"),
    ("MTSCEnabled", "0" if FrogsGoMoo else "1"),
    ("MuteDM", "1" if FrogsGoMoo else "0"),
    ("MuteDoor", "1" if FrogsGoMoo else "0"),
    ("MuteOverheated", "1" if FrogsGoMoo else "0"),
    ("MuteSeatbelt", "1" if FrogsGoMoo else "0"),
    ("NNFF", "1"),
    ("NoLogging", "0"),
    ("NudgelessLaneChange", "1"),
    ("NumericalTemp", "1" if FrogsGoMoo else "0"),
    ("Offset1", "5"),
    ("Offset2", "7" if FrogsGoMoo else "5"),
    ("Offset3", "10" if FrogsGoMoo else "5"),
    ("Offset4", "20" if FrogsGoMoo else "10"),
    ("OneLaneChange", "1"),
    ("PathEdgeWidth", "20"),
    ("PathWidth", "61"),
    ("PauseLateralOnSignal", "0"),
    ("PersonalitiesViaScreen", "0" if FrogsGoMoo else "1"),
    ("PersonalitiesViaWheel", "1"),
    ("PreferredSchedule", "0"),
    ("QOLControls", "1"),
    ("QOLVisuals", "1"),
    ("RandomEvents", "1" if FrogsGoMoo else "0"),
    ("RelaxedFollow", "30" if FrogsGoMoo else "18"),
    ("RelaxedJerk", "50" if FrogsGoMoo else "10"),
    ("ReverseCruise", "0"),
    ("ReverseCruiseUI", "0"),
    ("RoadEdgesWidth", "2"),
    ("RoadNameUI", "1"),
    ("RotatingWheel", "1"),
    ("ScreenBrightness", "101"),
    ("SearchInput", "0"),
    ("SetSpeedOffset", "0"),
    ("ShowCPU", "1" if FrogsGoMoo else "0"),
    ("ShowGPU", "0"),
    ("ShowMemoryUsage", "1" if FrogsGoMoo else "0"),
    ("Sidebar", "1" if FrogsGoMoo else "0"),
    ("SilentMode", "0"),
    ("SLCFallback", "2"),
    ("SLCOverride", "1"),
    ("SLCPriority1", "1"),
    ("SLCPriority2", "2"),
    ("SLCPriority3", "3"),
    ("SmoothBraking", "1"),
    ("SNGHack", "0" if FrogsGoMoo else "1"),
    ("SpeedLimitController", "1"),
    ("StandardFollow", "15"),
    ("StandardJerk", "10"),
    ("StoppingDistance", "3" if FrogsGoMoo else "0"),
    ("TSS2Tune", "1"),
    ("TurnAggressiveness", "150" if FrogsGoMoo else "100"),
    ("TurnDesires", "1" if FrogsGoMoo else "0"),
    ("UnlimitedLength", "1"),
    ("UseSI", "1" if FrogsGoMoo else "0"),
    ("UseVienna", "0"),
    ("VisionTurnControl", "1"),
    ("WheelIcon", "1" if FrogsGoMoo else "3")
  ]
  if not PC:
    default_params.append(("LastUpdateTime", datetime.datetime.utcnow().isoformat().encode('utf8')))

  if params.get_bool("RecordFrontLock"):
    params.put_bool("RecordFront", True)

  # set unset params
  for k, v in default_params:
    if params.get(k) is None:
      params.put(k, v)

  # Remove this after the June 14th update
  previous_speed_limit = params.get_float("PreviousSpeedLimit")
  if previous_speed_limit >= 50:
    params.put_float("PreviousSpeedLimit", previous_speed_limit / 100)

  slc_priority = params.get_int("SLCPriority")
  if slc_priority != 0:
    priorities_mapping = {
      1: ["Dashboard", "Navigation", "Offline Maps"],
      2: ["Navigation", "Offline Maps", "Dashboard"],
      3: ["Navigation", "Offline Maps", "None"],
      4: ["Navigation", "Dashboard", "None"],
      5: ["Navigation", "None", "None"],
      6: ["Offline Maps", "Dashboard", "Navigation"],
      7: ["Offline Maps", "Navigation", "Dashboard"],
      8: ["Offline Maps", "Navigation", "None"],
      9: ["Offline Maps", "Dashboard", "None"],
      10: ["Offline Maps", "None", "None"],
      11: ["Dashboard", "Navigation", "Offline Maps"],
      12: ["Dashboard", "Offline Maps", "Navigation"],
      13: ["Dashboard", "Offline Maps", "None"],
      14: ["Dashboard", "Navigation", "None"],
      15: ["Dashboard", "None", "None"],
      16: ["Highest", "None", "None"],
      17: ["Lowest", "None", "None"],
      18: ["None", "None", "None"],
    }

    primary_priorities = ["None", "Dashboard", "Navigation", "Offline Maps", "Highest", "Lowest"]
    old_priorities = priorities_mapping.get(slc_priority + 1, ["None", "None", "None"])

    for i, priority in enumerate(old_priorities, start=1):
      params.put_float(f"SLCPriority{i}", primary_priorities.index(priority))
      params.put_int("SLCPriority", 0)

  # Create folders needed for msgq
  try:
    os.mkdir("/dev/shm")
  except FileExistsError:
    pass
  except PermissionError:
    print("WARNING: failed to make /dev/shm")

  # set version params
  params.put("Version", get_version())
  params.put("TermsVersion", terms_version)
  params.put("TrainingVersion", training_version)
  params.put("GitCommit", get_commit(default=""))
  params.put("GitBranch", get_short_branch(default=""))
  params.put("GitRemote", get_origin(default=""))
  params.put_bool("IsTestedBranch", is_tested_branch())
  params.put_bool("IsReleaseBranch", is_release_branch())

  # set dongle id
  reg_res = register(show_spinner=True)
  if reg_res:
    dongle_id = reg_res
  else:
    serial = params.get("HardwareSerial")
    raise Exception(f"Registration failed for device {serial}")
  os.environ['DONGLE_ID'] = dongle_id  # Needed for swaglog

  if not is_dirty():
    os.environ['CLEAN'] = '1'

  # init logging
  sentry.init(sentry.SentryProject.SELFDRIVE)
  cloudlog.bind_global(dongle_id=dongle_id,
                       version=get_version(),
                       origin=get_normalized_origin(),
                       branch=get_short_branch(),
                       commit=get_commit(),
                       dirty=is_dirty(),
                       device=HARDWARE.get_device_type())

  # preimport all processes
  for p in managed_processes.values():
    p.prepare()

  # Set the desired model
  set_model(params)

def manager_cleanup() -> None:
  # send signals to kill all procs
  for p in managed_processes.values():
    p.stop(block=False)

  # ensure all are killed
  for p in managed_processes.values():
    p.stop(block=True)

  cloudlog.info("everything is dead")


def manager_thread() -> None:
  cloudlog.bind(daemon="manager")
  cloudlog.info("manager start")
  cloudlog.info({"environ": os.environ})

  params = Params()

  ignore: List[str] = []
  if params.get("DongleId", encoding='utf8') in (None, UNREGISTERED_DONGLE_ID):
    ignore += ["manage_athenad", "uploader"]
  if os.getenv("NOBOARD") is not None:
    ignore.append("pandad")
  ignore += [x for x in os.getenv("BLOCK", "").split(",") if len(x) > 0]

  sm = messaging.SubMaster(['deviceState', 'carParams'], poll=['deviceState'])
  pm = messaging.PubMaster(['managerState'])

  write_onroad_params(False, params)
  ensure_running(managed_processes.values(), False, params=params, CP=sm['carParams'], not_run=ignore)

  started_prev = False

  while True:
    sm.update()

    started = sm['deviceState'].started

    if started and not started_prev:
      params.clear_all(ParamKeyType.CLEAR_ON_ONROAD_TRANSITION)
    elif not started and started_prev:
      params.clear_all(ParamKeyType.CLEAR_ON_OFFROAD_TRANSITION)

    # update onroad params, which drives boardd's safety setter thread
    if started != started_prev:
      write_onroad_params(started, params)

    started_prev = started

    ensure_running(managed_processes.values(), started, params=params, CP=sm['carParams'], not_run=ignore)

    running = ' '.join("%s%s\u001b[0m" % ("\u001b[32m" if p.proc.is_alive() else "\u001b[31m", p.name)
                       for p in managed_processes.values() if p.proc)
    print(running)
    cloudlog.debug(running)

    # send managerState
    msg = messaging.new_message('managerState', valid=True)
    msg.managerState.processes = [p.get_process_state_msg() for p in managed_processes.values()]
    pm.send('managerState', msg)

    # Exit main loop when uninstall/shutdown/reboot is needed
    shutdown = False
    for param in ("DoUninstall", "DoShutdown", "DoReboot"):
      if params.get_bool(param):
        shutdown = True
        params.put("LastManagerExitReason", f"{param} {datetime.datetime.now()}")
        cloudlog.warning(f"Shutting down manager - {param} set")

    if shutdown:
      break


def main() -> None:
  manager_init()
  if os.getenv("PREPAREONLY") is not None:
    return

  # Remove the prebuilt file to prevent boot failures
  if os.path.exists(PREBUILT_FILE):
    os.remove(PREBUILT_FILE)

  # SystemExit on sigterm
  signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(1))

  try:
    manager_thread()
  except Exception:
    traceback.print_exc()
    sentry.capture_exception()
  finally:
    manager_cleanup()

  params = Params()
  if params.get_bool("DoUninstall"):
    cloudlog.warning("uninstalling")
    HARDWARE.uninstall()
  elif params.get_bool("DoReboot"):
    cloudlog.warning("reboot")
    HARDWARE.reboot()
  elif params.get_bool("DoShutdown"):
    cloudlog.warning("shutdown")
    HARDWARE.shutdown()


if __name__ == "__main__":
  unblock_stdout()

  try:
    main()
  except KeyboardInterrupt:
    print("got CTRL-C, exiting")
  except Exception:
    add_file_handler(cloudlog)
    cloudlog.exception("Manager failed to start")

    try:
      managed_processes['ui'].stop()
    except Exception:
      pass

    # Show last 3 lines of traceback
    error = traceback.format_exc(-3)
    error = "Manager failed to start\n\n" + error
    with TextWindow(error) as t:
      t.wait_for_exit()

    raise

  # manual exit because we are forked
  sys.exit(0)
