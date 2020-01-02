from mycroft import MycroftSkill, intent_file_handler, util
from collections import defaultdict
import json
import logging
import datetime

DEADLINE_FILE = 'deadlines.json'
class DeadlineTracker(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        self._deadlines = defaultdict(dict)
        self._deadlines.update(self._read_deadline_data())

    def _read_deadline_data(self):
        try:
            with self.file_system.open(DEADLINE_FILE, 'r') as conf_file:
                return json.loads(conf_file.read())
        except FileNotFoundError:
            logging.error('Deadlines file not found')
        except PermissionError:
            logging.error('Permission denied when reading Deadlines file')
        except json.decoder.JSONDecodeError:
            logging.error('Error decoding JSON file')
        logging.info('Initializing empty dictionary')
        return {}

    def _write_deadline_data(self):
        with self.file_system.open(DEADLINE_FILE, 'w') as conf_file:
            conf_file.write(json.dumps(self._deadlines, indent=4))


    @intent_file_handler('create.deadline.intent')
    def add_deadline(self, message):
        name = self.get_response('deadline.name')
        if not name:
            return
        name = name.lower()
        if name in 'cancel':
            return
        
        deadline_details = self._get_deadline_details()
        if not deadline_details:
            return
        
        self._deadlines[name]['detail'] = str(deadline_details)
        self._write_deadline_data()
        self.speak_dialog('created.deadline', data={'name':name})



    def _get_deadline_details(self):
        date = self.get_response('get.deadline.date')
        if not date:
            return []
        date = date.lower()
        if date in 'cancel':
            return []
        parsed_date = util.parse.extract_datetime(date)
        return parsed_date[0]



    @intent_file_handler('tracker.deadline.intent')
    def list_deadline(self, message):
        if not self._deadlines:
            self.speak_dialog('no.deadlines')
            return
        number = 0
        for item in self._deadlines:
            today = datetime.date.today()
            deadline_date_obj = datetime.datetime.strptime(self._deadlines[item].get('detail'), '%Y-%m-%d %H:%M:%S%z')
            deadline_date = deadline_date_obj.date()
            if (deadline_date - today).days <= 5:
                number = number + 1
                
        self.speak_dialog('tracker.deadline', data={'number': number})

    


def create_skill():
    return DeadlineTracker()

