from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from pourover.models import BrewProfile
import json


class MyConsumer(WebsocketConsumer):
    group_name = 'pourover_group'
    channel_name = 'pourover_channel'

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()

        self.start_brew()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )

    def receive(self, **kwargs):
        if 'text_data' not in kwargs:
            self.send_error('you must send text_data')
            return

        try:
            data = json.loads(kwargs['text_data'])
        except json.JSONDecoder:
            self.send_error('invalid JSON sent to server')
            return

        if 'action' not in data:
            self.send_error('action property not sent in JSON')
            return

        action = data['action']

        if action == 'add':
            self.received_add(data)
            return

        if action == 'delete':
            self.received_delete(data)
            return

        self.send_error(f'Invalid action property: "{action}"')

    def received_add(self, data):
        if 'text' not in data:
            self.send_error('"text" property not sent in JSON')
            return

        text = data['text']
        new_item = Item(text=text, ip_addr=self.scope['client'][0], user=self.user)
        new_item.save()

        self.broadcast_list()

    def received_delete(self, data):
        if 'id' not in data:
            self.send_error('id property not sent in JSON')
            return

        try:
            item = Item.objects.get(id=data['id'])
        except Item.DoesNotExist:
            self.send_error(f"Item with id={data['id']} does not exist")
            return

        if self.user.id != item.user.id:
            self.send_error("You cannot delete other user's entries")
            return

        item.delete()
        self.broadcast_list()

    def send_error(self, error_message):
        self.send(text_data=json.dumps({'error': error_message}))

    def broadcast_list(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps(Item.make_item_list())
            }
        )

    def broadcast_event(self, event):
        self.send(text_data=event['message'])
