from hdmi_optimizer.cli import criar_parser_monitor, main_monitor
from hdmi_optimizer.monitoring.service import monitorar_nvidia


def criar_parser():
    return criar_parser_monitor()


def main(argv=None):
    return main_monitor(argv)


if __name__ == "__main__":
    raise SystemExit(main())
