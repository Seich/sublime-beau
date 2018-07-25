import json
import platform
import sublime_plugin
import subprocess
import sublime
from .status_loops import loop_status_msg
from threading import Thread
from http.client import responses
from sublime import load_settings, active_window
from subprocess import check_output

SETTINGS_FILE = 'Beau.sublime-settings'
SYNTAX = 'Packages/JavaScript/JSON.sublime-syntax'

is_windows = (platform.system() == 'Windows')

class InsertTextCommand(sublime_plugin.TextCommand):
	def run(self, edit, text):
		self.view.insert(edit, 0, text)

class BeauCommand(sublime_plugin.TextCommand):
	requests = []
	path = ''
	active_view = None
	scope = None
	folders = []
	stop = None

	def inThread(self, command, onComplete, cwd=None):
		def thread(command, onComplete):
			try:
				self.stop = loop_status_msg([' ⣾', ' ⣽', ' ⣻', ' ⢿', ' ⡿', ' ⣟', ' ⣯', ' ⣷'], .1)
				proc = check_output(command, shell=is_windows, stderr=subprocess.STDOUT, cwd=cwd)
				onComplete(proc)
				return
			except subprocess.CalledProcessError as e:
				self.stop()
				sublime.set_timeout_async(lambda: active_window().status_message('Beau Command Failed. Open the console for more info.'), 1000)
				print(e.output)

		thread = Thread(target=thread, args=(command, onComplete))
		thread.start()

		return thread

	def run(self, edit):
		settings = load_settings(SETTINGS_FILE)
		self.path = settings.get('cli_path', '')
		self.active_view = active_window().active_view()
		self.folders = active_window().folders()

		self.scope = self.active_view.scope_name(self.active_view.sel()[0].b)
		command = [self.path, 'list', '--no-format']
		if self.scope.startswith('source.yaml'):
			command.extend(['-c', self.active_view.file_name()])

		self.inThread(
			command,
			self.listFetched,
			cwd=self.folders[0] if len(self.folders) > 0 else None
		)

	def listFetched(self, list):
		self.stop(True)

		requests = []
		self.requests[:] = []
		for line in list.splitlines():
			req = line.decode('utf-8').rstrip().split('\t')
			method, alias, endpoint = req
			requests.append([alias, endpoint])
			self.requests.append(req)

		active_window().show_quick_panel(requests, self.on_request_selected)

	def on_request_selected(self, index):
		if index == -1:
			return

		method, alias, endpoint = self.requests[index]

		active_window().status_message('Running: ' + alias)

		def handleResult(result):
			self.stop(True)

			response = []
			for line in result.splitlines():
				response.append(line.rstrip())

			active_window().status_message('')

			status, endpoint, headers, body = response

			status = status.decode('utf-8')
			endpoint = endpoint.decode('utf-8')
			headers = headers.decode('utf-8')
			body = body.decode('utf-8')

			results_view = active_window().new_file()
			results_view.set_name('Results: ' + alias)

			content = method + ' ' + endpoint + '\n'
			content += status + ' ' + responses[int(status)] + '\n\n'

			content += 'Response Headers: \n'
			content += self.autoindent(headers)

			content += '\n\nResponse Body: \n'
			content += self.autoindent(body)

			results_view.run_command('insert_text', {'text': content})
			results_view.set_scratch(True)
			results_view.set_syntax_file(SYNTAX)

		command = [self.path, 'request', alias, '--no-format']
		if self.scope.startswith('source.yaml'):
			command.extend(['-c', self.active_view.file_name()])

		self.inThread(
			command,
			onComplete=handleResult,
			cwd=self.folders[0] if len(self.folders) > 0 else None
		)

	def autoindent(self, obj):
		if not obj.strip():
			return 'Empty';

		parsed = json.loads(obj)
		return json.dumps(
			parsed,
			sort_keys=True,
			indent='\t',
			separators=(',', ': '),
			ensure_ascii=False
		)

	def is_windows(self):
		return platform.system() == 'Windows'

