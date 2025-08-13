"""
Station Action Interface
"""

class StationActionInterface:
    def __init__(self, config):
        self.config = config
        self.visible = False
        self.selected_station = None
        
    def show_for_station(self, station_name, station_info, actions, position):
        self.selected_station = station_name
        self.visible = True
        
    def hide(self):
        self.visible = False
        self.selected_station = None
        
    def handle_mouse_motion(self, pos):
        pass
        
    def handle_mouse_click(self, pos, button):
        return None
        
    def handle_keyboard_input(self, key):
        return None
        
    def render(self, surface, station_info=None):
        pass
        
    def render_quick_actions(self, surface, station_name, actions):
        pass
        
    def is_visible(self):
        return self.visible
        
    def get_selected_station(self):
        return self.selected_station