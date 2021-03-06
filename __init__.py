
from mycroft import MycroftSkill, intent_file_handler, util
from collections import defaultdict
import json
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

DEADLINE_FILE = 'deadlines.json'
class DeadlineTracker(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self._deadlines = defaultdict(dict)
        self._deadlines.update(self._read_deadline_data())

    def _read_deadline_data(self):
        try:
            with self.file_system.open(DEADLINE_FILE, 'r') as conf_file:
                return json.loads(conf_file.read())
        except FileNotFoundError:
            util.LOG.error('Deadlines file not found')
        except PermissionError:
            util.LOG.error('Permission denied when reading Deadlines file')
        except json.decoder.JSONDecodeError:
            util.LOG.error('Error decoding JSON file')
        util.LOG.info('Initializing empty dictionary')
        return {}

    def _write_deadline_data(self):
        with self.file_system.open(DEADLINE_FILE, 'w') as conf_file:
            conf_file.write(json.dumps(self._deadlines, indent=4))

    def _scheduler(self):
        for deadline in self._deadlines:
            self._register_deadline(deadline)

    def _register_deadline(self, deadline):
        time = datetime.datetime.strptime(self._deadlines[deadline].get('detail'))
        job = self.scheduler.add_job(func=self._schedule_handler, run_date=time, args=[deadline])
        util.LOG.info('deadline-tracker-skill: Created deadline for %s with jobID: %s', deadline, job.id)
    
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
        if (self.speak_dialog('created.deadline', data={'name':name})):
            time = datetime.datetime.strptime(self._deadlines[name].get('detail'))
            job = self.scheduler.add_job(func=self._schedule_handler, run_date=time, args=[name])
            util.LOG.info('deadline-tracker-skill: Created deadline for %s with jobID: %s', name, job.id)
        
    def _get_deadline_details(self):
        date = self.get_response('get.deadline.date')
        if not date:
            return []
        date = date.lower()
        if date in 'cancel':
            return []
        parsed_date = util.parse.extract_datetime(date)
        return parsed_date[0]

    def _schedule_handler(self, message):
        self.speak_dialog('scheduled.now',data={'itemName': message})
        

    @intent_file_handler('tracker.deadline.intent')
    def list_deadline(self, message):
        if not self._deadlines:
            self.speak_dialog('no.deadlines')
            return
        self.speak_dialog('These are your nearest deadlines')
        for item in self._deadlines:
            today = datetime.date.today()
            deadline_date_obj = datetime.datetime.strptime(self._deadlines[item].get('detail'), '%Y-%m-%d %H:%M:%S%z')
            deadline_date = deadline_date_obj.date()
            if (deadline_date - today).days <= 5:
                humanized_date = deadline_date_obj.strftime('%d %B %I %M %p')
                self.speak_dialog('deadline.list', data = {'deadline': item, 'date': humanized_date})


    @intent_file_handler('number.deadline.intent')
    def number_of_deadline(self):
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
        self.speak_dialog('tracker.deadline', data = {'number': number})

    @intent_file_handler('delete.item.intent')
    def delete_item(self, message):
        item = message.data['name']
        del(self._deadlines[item])
        self._write_deadline_data()
        self.speak_dialog('item.deleted', data = {'item':item})



def create_skill():
    return DeadlineTracker()

