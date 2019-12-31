from mycroft import MycroftSkill, intent_file_handler


class DeadlineTracker(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('tracker.deadline.intent')
    def handle_tracker_deadline(self, message):
        number = ''

        self.speak_dialog('tracker.deadline', data={
            'number': number
        })


def create_skill():
    return DeadlineTracker()

