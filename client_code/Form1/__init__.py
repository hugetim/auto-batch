from ._anvil_designer import Form1Template
from anvil import *
import anvil.server


class Form1(Form1Template):

  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.

  def form_show(self, **event_args):
    """This method is called when the HTML panel is shown on the screen"""
    anvil.server.call('write_id_to_table')

  def timer_1_tick(self, **event_args):
    """This method is called Every [interval] seconds. Does not trigger if [interval] is 0."""
    anvil.server.call('write_id_to_table')


