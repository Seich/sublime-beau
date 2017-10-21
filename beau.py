import json
import sublime
import sublime_plugin
from http.client import responses
from subprocess import Popen, PIPE

PLUGIN_NAME = 'Beau'
SETTINGS_FILE = '{0}.sublime-settings'.format(PLUGIN_NAME)
SYNTAX = 'Packages/JavaScript/JSON.sublime-syntax'
settings = sublime.load_settings(SETTINGS_FILE)

class InsertTextCommand(sublime_plugin.TextCommand):
	def run(self, edit, text):
		self.view.insert(edit, 0, text)


class BeauCommand(sublime_plugin.TextCommand):
	requests = []
	path = settings.get('cli_path', '')

	def run(self, edit):
		active_window = sublime.active_window()
		active_view = active_window.active_view()

		scope = active_view.scope_name(active_view.sel()[0].b)
		if not scope.startswith('source.yaml'):
			active_window.status_message('Beau can only be ran on yaml files.')
			return

		proc = Popen([
			self.path,
			'-c',
			active_view.file_name(),
			'--clean-list'
		], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)

		for line in iter(proc.stderr.readline, b''):
			print(line)
			active_window.status_message(line.decode("utf-8"))

		requests = []
		self.requests[:] = []
		for line in iter(proc.stdout.readline, b''):
			req = line.decode('utf-8').rstrip().split('\t')
			method, alias, endpoint = req
			self.requests.append(req)
			requests.append([alias, endpoint])

		proc.wait()
		active_window.show_quick_panel(requests, self.on_done)

	def on_done(self, index):
		active_window = sublime.active_window()
		active_view = active_window.active_view()

		method, alias, endpoint = self.requests[index]

		active_window.status_message('Executing: ' + alias)

		proc = Popen([
			self.path,
			'-c',
			active_view.file_name(),
			'-R',
			alias
		], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)

		response = []
		for line in iter(proc.stdout.readline, b''):
			response.append(line.rstrip())

		status, endpoint, headers, body = response

		status = status.decode('utf-8')
		endpoint = endpoint.decode('utf-8')
		headers = headers.decode('utf-8')
		body = body.decode('utf-8')

		results_view = active_window.new_file()
		results_view.set_name('Results: ' + alias)

		content = method + ' ' + endpoint + '\n'
		content += status + ' ' + responses[int(status)] + '\n\n'
		content += 'Response Headers: \n'
		content += self.autoindent(headers)
		content += '\n\n Response Body: \n'
		content += self.autoindent(body)

		results_view.run_command('insert_text', {'text': content})
		results_view.set_scratch(True)
		results_view.set_syntax_file(SYNTAX)

	def autoindent(self, obj):
		parsed = json.loads(obj)
		return json.dumps(
			parsed,
			sort_keys=True,
			indent='\t',
			separators=(',', ': '),
			ensure_ascii=False
		)
