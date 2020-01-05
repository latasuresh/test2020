import errno
import os
import re
import shutil
import zipfile
from zipfile import ZipFile

from PIL.PngImagePlugin import PngImageFile, PngInfo

from automations.utils.log import Log

SAMPLE_IMAGE = "automations/res/sample_image.png"
PRIVATE_APP_PATH = "automations/res/private_app.zip"
JSON_RENDERER = "json_renderer.js"
TMP_PATH = os.path.join(os.getcwd(), "tmp")
OUTPUT_PATH = os.path.join(os.getcwd(), "output")
JSON_TEMPLATE_PATH = os.path.join(os.getcwd(), "automations", "res", "json_template.html")
JSON_RENDERER_PATH = os.path.join(os.getcwd(), "automations", "res", JSON_RENDERER)

class FileSupport(dict):
	"""Helper for file operations, assumes invocation is always from the root
	of the repo.
	"""

	temp_files = []

	@classmethod
	def init_file_support(cls):
		cls.original_sample_image_path = os.path.abspath(SAMPLE_IMAGE)
		cls.create_directory(TMP_PATH)
		cls.create_directory(OUTPUT_PATH)

	@classmethod
	def cleanup_file_support(cls):
		"""Remove all files generated.
		"""
		for file in cls.temp_files:
			try:
				os.remove(file)
			except:
				Log.logger.warn("Failed to remove temp file: {}".format(file))
		cls.temp_files = []

	def sample_image_path(self):
		"""Copy the sample image to to a unique file name and return the path.

		Returns:
			tuple of (the filename, the new sample image path)
		"""
		filename = self.generate_alphanumeric() + ".png"
		new_file = self.tmp_file_path(filename)
		shutil.copy(self.original_sample_image_path, new_file)

		# make the image content unique
		image_file = PngImageFile(open(new_file, "r"))
		info = PngInfo()
		info.add_text('Comment', self.generate_alphanumeric(length=30))
		image_file.save(new_file, pnginfo=info)
		self.temp_files.append(new_file)
		return (filename, new_file)

	def sample_text_file(self):
		"""Create a random text file
		"""
		file_name = self.generate_msg() + '.txt'
		file_path = self.tmp_file_path(file_name)
		with open(file_path, 'a') as f:
			f.write(self.generate_msg())
		return (file_name, file_path)

	def private_app_path(self):
		"""Get the absolute path of the sample private app.

		Returns:
			the path of the sample private app
		"""
		return os.path.abspath(PRIVATE_APP_PATH)

	def tmp_file_path(self, filename):
		"""Generate a new temp file path.

		Args:
			filename (str): the file extension

		Returns:
			the new randomised file path
		"""
		return os.path.join(TMP_PATH, filename)

	def remove_failure_zip(self, test_name):
		"""Remove any pre-existing test zip before saving new failure data.

		Args:
			test_name (str): the test method name
		"""
		zip_path = self.zip_path(test_name)
		if os.path.exists(zip_path):
			os.remove(zip_path)

	def save_page_html(self, test_name, driver_name, page_sources):
		"""Save the full (or partial) page HTML string to a file in 'output'.

		Args:
			test_name (str): the test method name
			driver_name (str): the name of the driver being saved
			(str, [str]): the base page source and an array of frame sources
		"""
		page_source = page_sources[0]
		iframes = page_sources[1]
		iframe_regex = r'<iframe([^>]*src=")[^"]*"'
		replacement_template = "<wibble\\1{}\""

		index = 1
		for iframe in iframes:
			filename = "frames/" + self.get_html_file_name(test_name, driver_name, index)
			self._save_to_output_zip(test_name, filename, iframe)
			frame_replacement = replacement_template.format(filename)
			page_source = re.sub(iframe_regex, frame_replacement, page_source, 1)
			index += 1

		final_page_source = page_source.replace("<wibble", "<iframe")
		page_name = self.get_html_file_name(test_name, driver_name)
		self._save_to_output_zip(test_name, page_name, final_page_source)

	def save_json_datanode(self, test_name, driver_name, node_string):
		"""Save the JSON datanode to a file in 'output'.

		Args:
			test_name (str): the test method name
			driver_name (str): the name of the driver being saved
			node_string (str): the JSON string of the datanode
		"""
		json_placeholder = 'node_content'
		filename = self.get_html_file_name(test_name, driver_name, "Datanode")
		with open(JSON_TEMPLATE_PATH, 'r') as node_file:
			page = node_file.read().replace(json_placeholder, node_string)
			self._save_to_output_zip(test_name, filename, page)

	def _save_to_output_zip(self, test_name, filename, content):
		"""Save source or datanode output to a Zip file.

		Args:
			filename (str): the filename to be saved
			content (str): the content of the page to save
		"""
		path = os.path.join(OUTPUT_PATH, filename)
		zip_path = self.zip_path(test_name)
		new_zip = not os.path.exists(zip_path)

		with ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as test_zip:
			test_zip.writestr(filename, content)
			if new_zip:
				with open(JSON_RENDERER_PATH, 'r') as js_file:
					test_zip.writestr(JSON_RENDERER, js_file.read())

	def zip_path(self, test_name):
		"""Get the zip file path for the test.

		Returns:
			str: the path
		"""
		return os.path.join(OUTPUT_PATH, test_name + ".zip")

	def get_html_file_name(self, test_name, driver_name, suffix=None):
		"""Get the full name of the html file to be saved be saved.

		Args:
			test_name (str): the full test name
			driver_name (str): the name of the driver being saved
			suffix (str): file name suffix if desired

		Returns:
			html file name for the content to be saved into
		"""
		if suffix:
			return "{}-{}_{}.html".format(test_name, driver_name, suffix)
		return "{}-{}.html".format(test_name, driver_name)


	@classmethod
	def create_directory(cls, path):
		"""Create a new directory if it does not exist.

		Args:
			path (str): the absolute path of the desired directory
		"""
		try:
			os.makedirs(path)
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise

	@staticmethod
	def read_file(path):
		"""Read file content from given path

		Args:
			path (str): the absolute path of the desired file
		"""
		with open(path, 'r') as f:
			return f.read()
