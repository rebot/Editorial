#coding: utf-8
import ui
import io
import time
import editor
import photos
import console
import workflow

class PathView (ui.View):
    def __init__(self, frame):
        self.frame = frame
        self.flex = 'WH'
        self.path = None
        self.action = None

    def touch_began(self, touch):
        x, y = touch.location
        self.path = ui.Path()
        self.path.line_width = 3.0
        self.path.line_join_style = ui.LINE_JOIN_ROUND
        self.path.line_cap_style = ui.LINE_CAP_ROUND
        self.path.move_to(x, y)

    def touch_moved(self, touch):
        x, y = touch.location
        self.path.line_to(x, y)
        self.set_needs_display() # redraw content

    def touch_ended(self, touch):
        # Send the current path to the SketchView:
        if callable(self.action):
            self.action(self)
        # Clear the view (the path has now been rendered
        # into the SketchView's image view):
        self.path = None
        self.set_needs_display() # redraw content

    def draw(self):
        if self.path:
        		ui.set_color('white')
        		self.path.stroke()

class SketchView (ui.View):
    def __init__(self):
        width, height = ui.get_window_size()
        canvas_size = max(width, height)
        frame = (0, 0, canvas_size, canvas_size)
        self.background_color = (0, 0, 0, 1)
        self.tint_color = 'white' #274197'
        iv = ui.ImageView(frame=frame)
        iv.background_color = (0, 0, 0, 0)
        pv = PathView(frame=self.bounds)
        pv.background_color = (0, 0, 0, 0)
        pv.action = self.path_action
        self.add_subview(iv)
        self.add_subview(pv)
        self.image_view = iv
        self.history = []

    def path_action(self, sender):
        path = sender.path
        self.history.append(self.image_view.image)
        width, height = self.image_view.width, self.image_view.height
        with ui.ImageContext(width, height) as ctx:
            if self.history[-1]:
                self.history[-1].draw()
            ui.set_color('white')
            path.stroke()
            self.image_view.image = ctx.get_image()

    def revert_action(self, sender):
        if len(self.history) > 0:
            self.image_view.image = self.history.pop()

    def clear_action(self, sender):
        self.image_view.image = None

    @ui.in_background
    def save_action(self, sender):
        if self.image_view.image:
            # We draw a new image here, so that it has the current
            # orientation (the canvas is quadratic).
            filename = time.strftime('%Y%m%d%H%M%S') + '.png'
            with ui.ImageContext(self.width, self.height) as ctx:
                self.image_view.image.draw()
                img = ctx.get_image()
                buffer = io.BytesIO() #(buffer, 'png')
                editor.set_file_contents(filename, img.to_png(), 'dropbox')
                editor.insert_text('![test](../' + filename + ')')
                self.close()
        else:
            console.hud_alert('No Image', 'error')
        workflow.set_output('test')

v = SketchView()
back_button = ui.ButtonItem()
back_button.image = ui.Image.named('iob:ios7_undo_24')
back_button.action = v.revert_action
save_button = ui.ButtonItem()
save_button.title = 'Save Image'
save_button.action = v.save_action
clear_button = ui.ButtonItem()
clear_button.title = 'Clear'
clear_button.tint_color = '#526172'
clear_button.action = v.clear_action
v.right_button_items = [save_button, clear_button, back_button]
v.present('fullscreen', title_bar_color='black')
v = v.objc_instance
for _ in range(1, 5): 
	v = v.superview()
	if v and v.gestureRecognizers():
		v.gestureRecognizers()[0].setEnabled(False)