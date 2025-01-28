
LOG_OUTPUT = False
LOG_DEBUG = False
LOG_INPUT = False
LOG_GAME = False
LOG_RESULTS = False


def log_general_msg(msg):
    if LOG_DEBUG or LOG_GAME or LOG_INPUT or LOG_OUTPUT:
        print(msg)


def _log(flag, player, pre_msg, msg):
    if not flag:
        return
    msg = str(msg)
    if msg is None or len(msg.strip()) == 0:
        return

    if player is not None:
        pre_msg = "Player %s %s : " % (player.name, pre_msg)
    else:
        pre_msg = "All Player %s : " % pre_msg

    for line in msg.split('<br/>'):
        print(pre_msg + line)


def log_input_msg(player, msg):
    _log(LOG_INPUT, player, 'INPUT', msg)


def log_output_msg(player, msg):
    _log(LOG_OUTPUT, player, 'OUTPUT', msg)


def log_debug_msg(player, msg):
    _log(LOG_DEBUG, player, 'DEBUG', msg)


def log_game_msg(player, msg):
    _log(LOG_GAME, player, 'GAME', msg)


def log_results_msg(player, score):
    _log(LOG_RESULTS, player, 'SCORE', str(score))
