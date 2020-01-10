from PIL import Image, ImageFilter
import glob
import os
import json


class Merger:

    def __init__(self):
        self.load_settings()
        self.design_image = None
        self.design_image_resized = None
        self.main_image = None
        self.design_image_name = None
        self.merged_image = None
        self.offset = [0, 0]
        self.output_path = None
        self.display_image = None
        self.centre = [0, 0]
        self.ratio = 1.414196123147092
        self.set_size = (600, int(600 * self.ratio))
        self.step = 5
        self.output_append = "_applied"
        self.overwrite = True
        self.folder = None
        self.filenames = []

    def load_settings(self):
        try:
            settings = open("settings.json", 'r')
        except IOError:
            print("Settings file not found")
        except:
            print("Something else wrong with file")
        else:
            try:
                settings_dict = json.loads(settings.read())
            except json.JSONDecodeError:
                print("Bad json format")
            except:
                print("Something else wrong with json")
            else:
                self.step = settings_dict['step']
                self.output_append = settings_dict['output_append']
                self.overwrite = settings_dict['overwrite']
                return
        return

    def set_main_image(self, location) -> bool:
        try:
            self.main_image = Image.open(location)
        except IOError:
            print("error: can't set main image")
            return False
        return True

    def merge_current(self, centre=None) -> None:
        if self.design_image is not None and self.main_image is not None:
            if self.design_image_resized is None:
                self.resize_to_set_size()
            if centre is None:
                centre = self.find_centre()
            if self.offset != [0, 0]:
                centre = list(centre)
                centre[0] += self.offset[0]
                centre[1] += self.offset[1]
                centre = tuple(centre)
            self.merged_image = self.main_image.copy()
            self.merged_image.alpha_composite(self.design_image_resized, centre)
            self.display_image = None
        else:
            print("Error: images not set")
        return

    def read_designs(self, folder) -> None:
        try:
            self.filenames = glob.glob(os.path.join(folder, '*.png'))
        except Exception as err:
            print(err)
        if len(self.filenames) == 0:
            print("No designs found in this directory:", folder)
            return
        self.set_design_image(self.filenames[0])

    def set_design_folder(self, folder) -> None:
        self.folder = folder
        self.read_designs(folder)

    def merge_all(self, maxi=None, opacity=245) -> None:
        counter = 0
        if maxi is not None or maxi != 0:
            total_amount = str(maxi)
        else:
            total_amount = str(len(self.filenames))
        for filename in self.filenames:
            # pravalyt atminti del galimu siuksliu
            del self.design_image_resized
            del self.design_image
            del self.merged_image
            del self.display_image
            if not self.design_image_name == filename:
                self.set_design_image(filename)
            self.resize_to_set_size(opacity=opacity)
            # self.resize_for_hoodie(size)
            self.merge_current()
            self.write_to_file(self.output_path)
            counter += 1

            print(counter, "/", total_amount, os.path.basename(self.design_image_name))
            if (maxi is not None or maxi == 0) and counter >= maxi:
                return
        return

    def resize_for_hoodie(self, size=600, quality=True):
        if quality:
            filter_to_use = Image.LANCZOS
        else:
            filter_to_use = Image.NEAREST
        self.design_image_resized = self.design_image.resize((size, int(self.ratio * size)), filter_to_use)
        self.set_size = (size, int(self.ratio * size))

    def resize_to_set_size(self, size=None, quality=True, blur=True, opacity=245):
        if size is None:
            size = self.set_size
        if quality:
            filter_to_use = Image.LANCZOS
        else:
            filter_to_use = Image.NEAREST
        if self.design_image is None:
            print("Design image is not set")
        if self.main_image is None:
            print("Main image is not set")
        self.design_image_resized = self.design_image.resize(size, filter_to_use)
        # if blur:
        #     self.add_blur()
        if opacity < 255:
            self.change_opacity(opacity=opacity)
        self.merged_image = None
        self.display_image = None

    def set_design_image(self, location) -> bool:
        try:
            self.design_image = Image.open(location)
            self.design_image_name = os.path.basename(location)
            self.merged_image = None
            self.design_image_resized = None
        except IOError:
            print("Something very bad with design images")
            return False
        self.display_image = None
        return True

    def find_centre(self) -> (int, int):
        centre = (int((self.main_image.size[0] - self.design_image_resized.size[0]) / 2),
                  int((self.main_image.size[1] - self.design_image_resized.size[1]) / 2))
        return centre

    def get_display(self, size=350) -> Image:
        if self.merged_image is None:
            self.merge_current()
        if self.display_image is None:
            self.display_image = self.merged_image.resize((int(size / self.ratio), size))
        return self.display_image

    def set_output_path(self, path):
        self.output_path = path

    def write_to_file(self, path=None) -> None:
        if not os.path.exists(os.path.join(self.folder, "applied")):
            print("Creating folder for applied designs")
            try:
                os.mkdir(os.path.join(self.folder, "applied"))
            except OSError:
                print("Can't create a folder in your design folder: ", os.path.join(self.folder, "applied"))
                print("Please create a folder in your designs directory named: 'applied'")
                return
        if path is None:
            path = os.path.join(self.folder, "applied", os.path.splitext(self.design_image_name)[0] + self.output_append
                                + os.path.splitext(self.design_image_name)[1])
        else:
            path = os.path.join(path, os.path.splitext(self.design_image_name)[0] + self.output_append +
                                os.path.splitext(self.design_image_name)[1])
        if os.path.exists(path) and not self.overwrite:
            return
        if self.merged_image is None:
            self.merge_current()
        self.merged_image.save(path)

    def add_blur(self):
        self.merged_image = None
        self.display_image = None
        self.design_image_resized = self.design_image_resized.filter(ImageFilter.GaussianBlur(radius=1))
        return

    def change_opacity(self, opacity=245):
        data = self.design_image_resized.getdata()  # you'll get a list of tuples
        new_data = []
        for a in data:
            b = a[:3]
            b = b + (min(opacity, a[3]),)
            new_data.append(b)
        self.design_image_resized.putdata(new_data)
        return

    def move_up(self, step=None):
        if step is None:
            step = self.step
        # if self.set_size[1] - (self.offset[1] - step) * 2 < self.main_image.size[1]:
        #     print("Can't move this much up")
        self.offset[1] -= step
        self.merge_current()
        return

    def move_down(self, step=None):
        if step is None:
            step = self.step
        self.offset[1] += step
        self.merge_current()
        return

    def move_right(self, step=None):
        if step is None:
            step = self.step
        self.offset[0] += step
        self.merge_current()
        return

    def move_left(self, step=None):
        if step is None:
            step = self.step
        self.offset[0] -= step
        self.merge_current()
        return

    def increase_size(self, size):
        old_size = self.set_size[0]
        old_size += size
        if old_size > self.main_image.size[0] or int(old_size * self.ratio) > self.main_image.size[1]:
            print((old_size, int(old_size * self.ratio)), "<- new_size, main_image_size ->", self.main_image.size)
            print("Design can't be bigger than main image (in any dimensions)")
            return
        if (int(abs(self.offset[0]) * 2 + old_size) > self.main_image.size[0]) or \
                (int(abs(self.offset[1]) * 2 + old_size * self.ratio) > self.main_image.size[1]):
            print("Increased size of design does not fit in this place, try moving it closer to centre")
            return
        self.set_size = (old_size, int(old_size * self.ratio))
        self.resize_to_set_size()
        return

    def decrease_size(self, size):
        old_size = self.set_size[0]
        old_size -= size
        if old_size <= 0:
            print("Design size can't be less than 1, it is now:", self.set_size[0])
            return
        self.set_size = (old_size, int(old_size * self.ratio))
        self.resize_to_set_size()
        return
