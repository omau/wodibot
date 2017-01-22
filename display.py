from pyvirtualdisplay import Display


def get_virtual_display():
    display = Display(visible=0, size=(800, 600))
    display.start()
    return display


def stop_virtual_display(display):
    display.stop()
