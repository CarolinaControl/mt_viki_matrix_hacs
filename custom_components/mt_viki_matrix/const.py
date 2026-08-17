"""Constants for the MT-VIKI HDMI Matrix integration."""

DOMAIN = "mt_viki_matrix"

CONF_INPUTS = "inputs"
CONF_OUTPUTS = "outputs"
CONF_INPUT_NAMES = "input_names"
CONF_OUTPUT_NAMES = "output_names"

DEFAULT_PORT = 8080
DEFAULT_NAME = "MT-VIKI Matrix"

# Command syntax comes from the MT-VIKI HDMI matrix control protocol
# (RS232 115200-8-N-1 / TCP raw text on port 8080). Every command ends
# with a literal period.
CMD_TERMINATOR = "."
CMD_SWITCH = "{inp}X{out}."          # switch one input to one output
CMD_SWITCH_ALL = "{inp}All."         # switch one input to all outputs
CMD_CLOSE_OUTPUT = "0X{out}."        # blank/close a single output
CMD_CLOSE_ALL = "0All."              # blank/close all outputs
CMD_ONE_TO_ONE = "All1."             # reset to 1:1 mapping
CMD_SAVE_SCENE = "Save{scene}."      # save current state to scene 1-9
CMD_RECALL_SCENE = "Recall{scene}."  # recall scene 1-9
CMD_BEEP_ON = "BeepON."
CMD_BEEP_OFF = "BeepOFF."

RESPONSE_OK = "OK"
RESPONSE_ERR = "ERR"

SOCKET_TIMEOUT = 3.0
