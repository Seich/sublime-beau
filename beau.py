import json
import platform
import sublime_plugin
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

	def inThread(self, command, onComplete):
		def thread(command, onComplete):
			proc = check_output(command, shell=is_windows)
			onComplete(proc)
			return

		thread = Thread(target=thread, args=(command, onComplete))
		thread.start()

		return thread

	def run(self, edit):
		settings = load_settings(SETTINGS_FILE)
		self.path = settings.get('cli_path', '')
		active_view = active_window().active_view()

		scope = active_view.scope_name(active_view.sel()[0].b)
		if not scope.startswith('source.yaml'):
			active_window().status_message('Beau can only be ran on yaml files.')
			return

		self.inThread(
			[self.path, '-c', active_view.file_name(), 'list', '--no-format'],
			self.listFetched
		)

	def listFetched(self, list):
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

		active_view = active_window().active_view()
		method, alias, endpoint = self.requests[index]

		active_window().status_message('Running: ' + alias)

		def handleResult(result):
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

		self.inThread(
			[self.path, '-c', active_view.file_name(), 'request', alias, '--no-format'],
			onComplete=handleResult
		)

	def autoindent(self, obj):
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

