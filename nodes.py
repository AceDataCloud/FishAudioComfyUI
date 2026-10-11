"""Schema-backed ComfyUI nodes for the current FishAudioDify catalog.

Model and action selectors are first-class. Remaining Dify parameters use JSON,
which is validated by the copied published API contract before any request.
"""

from __future__ import annotations

import json
import os

from .client import AceDataFishClient

SERVICE = 'Fish Audio'
MEDIA_TYPES = ('AUDIO',)
TOOL_SPECS = {'fish_create_model': {'models': [],
                       'actions': [],
                       'operation': 'request',
                       'label': 'Fish Audio Create Model',
                       'description': 'Create Model through the Ace Data Cloud Fish Audio API.',
                       'required': ['title', 'voices'],
                       'fields': ['title',
                                  'voices',
                                  'description',
                                  'cover_image',
                                  'tags',
                                  'texts',
                                  'enhance_audio_quality',
                                  'generate_sample']},
 'fish_create_voice': {'models': [],
                       'actions': [],
                       'operation': 'request',
                       'label': 'Fish Audio Create Voice',
                       'description': 'Create Voice through the Ace Data Cloud Fish Audio API.',
                       'required': ['voice_url'],
                       'fields': ['voice_url', 'title', 'description', 'image_url', 'callback_url']},
 'fish_generate_audio': {'models': ['s1', 's2-pro', 's2.1-pro'],
                         'actions': [],
                         'operation': 'generate',
                         'label': 'Fish Generate Audio',
                         'description': 'Generate text-to-speech audio with the Ace Data Cloud Fish '
                                        'Audio API.',
                         'required': ['text'],
                         'fields': ['text',
                                    'reference_id',
                                    'format',
                                    'sample_rate',
                                    'mp3_bitrate',
                                    'latency',
                                    'chunk_length',
                                    'min_chunk_length',
                                    'temperature',
                                    'top_p',
                                    'repetition_penalty',
                                    'max_new_tokens',
                                    'normalize',
                                    'prosody',
                                    'references',
                                    'callback_url']},
 'fish_get_voice': {'models': [],
                    'actions': [],
                    'operation': 'request',
                    'label': 'Fish Audio Get Voice',
                    'description': 'Get Voice through the Ace Data Cloud Fish Audio API.',
                    'required': ['id'],
                    'fields': ['id']},
 'fish_search_voices': {'models': [],
                        'actions': [],
                        'operation': 'voices',
                        'label': 'Fish Search Voices',
                        'description': 'Fish Search Voices via Ace Data Cloud.',
                        'required': [],
                        'fields': ['limit',
                                   'page_number',
                                   'query',
                                   'tag',
                                   'self',
                                   'author_id',
                                   'language',
                                   'title_language',
                                   'sort_by']},
 'fish_task_retrieve': {'models': [],
                        'actions': [],
                        'operation': 'task',
                        'label': 'Fish Audio Retrieve Task',
                        'description': 'Retrieve one task, optionally waiting up to 240 seconds.',
                        'required': ['task_id'],
                        'fields': []},
 'fish_tasks_retrieve_batch': {'models': [],
                               'actions': [],
                               'operation': 'batch',
                               'label': 'Fish Audio Retrieve Tasks',
                               'description': 'Retrieve existing tasks by ID without repeating '
                                              'generation.',
                               'required': ['ids'],
                               'fields': []}}
SENTINEL = '(from JSON/default)'


def _credential() -> str:
    token = os.environ.get('ACEDATACLOUD_API_KEY') or os.environ.get('ACEDATACLOUD_API_TOKEN')
    if not token or not token.strip():
        raise RuntimeError('Set ACEDATACLOUD_API_KEY in the ComfyUI process environment and restart.')
    return token.strip()


class _ToolNode:
    RETURN_TYPES = ('STRING', 'STRING', 'STRING', 'STRING', 'STRING', 'STRING')
    RETURN_NAMES = ('status', 'task_id', 'media_urls_json', 'first_media_url', 'result_json', 'trace_id')
    FUNCTION = 'run'
    CATEGORY = 'Ace Data Cloud/' + SERVICE
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        spec = cls.SPEC
        required = {'parameters_json': ('STRING', {'multiline': True, 'default': '{}'})}
        if spec['models']:
            required['model'] = ([SENTINEL, *spec['models']], {'default': SENTINEL})
        if spec['actions']:
            required['action'] = ([SENTINEL, *spec['actions']], {'default': SENTINEL})
        for name in spec['fields']:
            if name == 'confirm':
                required[name] = ('BOOLEAN', {'default': False})
            else:
                required[name] = ('STRING', {'multiline': name in {'prompt', 'lyric', 'lyrics',
                    'image_urls', 'audio_urls', 'video_urls', 'negative_prompt'} or name.endswith('_json'),
                    'default': ''})
        if spec['operation'] == 'task':
            required['task_id'] = ('STRING', {'default': ''})
            required['wait_seconds'] = ('INT', {'default': 0, 'min': 0, 'max': 240})
        if spec['operation'] == 'batch':
            required['ids_json'] = ('STRING', {'multiline': True, 'default': ''})
        return {'required': required}

    def run(self, parameters_json: str, model: str = SENTINEL, action: str = SENTINEL,
            task_id: str = '', wait_seconds: int = 0, ids_json: str = '', **fields):
        try:
            parameters = json.loads(parameters_json)
        except (TypeError, ValueError):
            raise ValueError('parameters_json must contain a JSON object.') from None
        if not isinstance(parameters, dict):
            raise ValueError('parameters_json must contain a JSON object.')
        if model != SENTINEL:
            parameters['model'] = model
        if action != SENTINEL:
            parameters['action'] = action
        for name, value in fields.items():
            if value is not None and value != '':
                parameters[name] = value
        if task_id.strip():
            parameters['task_id'] = task_id.strip()
        if self.SPEC['operation'] == 'task':
            parameters['wait_seconds'] = wait_seconds
        if ids_json.strip():
            try:
                ids = json.loads(ids_json)
            except ValueError:
                raise ValueError('ids_json must be a JSON array of task IDs.') from None
            if not isinstance(ids, list) or not ids:
                raise ValueError('ids_json must be a nonempty JSON array of task IDs.')
            parameters['ids'] = ids
        result = AceDataFishClient(_credential()).invoke(self.TOOL, parameters)
        urls = result.get('media_urls') or []
        if not isinstance(urls, list):
            urls = []
        status = str(result.get('status') or 'unknown')
        resolved_task_id = str(result.get('task_id') or '')
        trace_id = str(result.get('trace_id') or '')
        return {
            'ui': {'text': [f'{SERVICE} status: {status}',
                            f'Task ID: {resolved_task_id or "completed synchronously"}',
                            f'Media URLs: {len(urls)}']},
            'result': (status, resolved_task_id, json.dumps(urls), urls[0] if urls else '',
                       json.dumps(result, ensure_ascii=False, default=str), trace_id),
        }


NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
for tool, spec in TOOL_SPECS.items():
    class_name = 'Ace' + ''.join(part.title() for part in SERVICE.split()) + ''.join(
        part.title() for part in tool.split('_')
    )
    node = type(class_name, (_ToolNode,), {'TOOL': tool, 'SPEC': spec,
                                          'DESCRIPTION': spec['description']})
    NODE_CLASS_MAPPINGS[class_name] = node
    NODE_DISPLAY_NAME_MAPPINGS[class_name] = spec['label'] + ' (Ace Data Cloud)'


if MEDIA_TYPES:
    from .media import as_audio, as_image, as_video, download_media


class _LoadImage:
    RETURN_TYPES = ('IMAGE',)
    RETURN_NAMES = ('image',)
    FUNCTION = 'run'
    CATEGORY = 'Ace Data Cloud/' + SERVICE
    DESCRIPTION = 'Load a completed Ace CDN image into ComfyUI IMAGE.'

    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'media_url': ('STRING', {'default': ''})}}

    def run(self, media_url: str):
        if not media_url:
            raise ValueError('Task is pending; retrieve the same task ID again.')
        return (as_image(download_media(media_url)),)


class _LoadVideo:
    RETURN_TYPES = ('VIDEO',)
    RETURN_NAMES = ('video',)
    FUNCTION = 'run'
    CATEGORY = 'Ace Data Cloud/' + SERVICE
    DESCRIPTION = 'Load a completed Ace CDN video into native ComfyUI VIDEO.'

    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'media_url': ('STRING', {'default': ''})}}

    def run(self, media_url: str):
        if not media_url:
            raise ValueError('Task is pending; retrieve the same task ID again.')
        return (as_video(download_media(media_url)),)


class _LoadAudio:
    RETURN_TYPES = ('AUDIO',)
    RETURN_NAMES = ('audio',)
    FUNCTION = 'run'
    CATEGORY = 'Ace Data Cloud/' + SERVICE
    DESCRIPTION = 'Load a completed Ace CDN audio file into ComfyUI AUDIO.'

    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'media_url': ('STRING', {'default': ''})}}

    def run(self, media_url: str):
        if not media_url:
            raise ValueError('Task is pending; retrieve the same task ID again.')
        return (as_audio(download_media(media_url)),)


for media_type, base in {'IMAGE': _LoadImage, 'VIDEO': _LoadVideo, 'AUDIO': _LoadAudio}.items():
    if media_type in MEDIA_TYPES:
        class_name = 'Ace' + ''.join(part.title() for part in SERVICE.split()) + 'Load' + media_type.title()
        NODE_CLASS_MAPPINGS[class_name] = type(class_name, (base,), {})
        NODE_DISPLAY_NAME_MAPPINGS[class_name] = SERVICE + ' Load ' + media_type.title() + ' (Ace Data Cloud)'

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'TOOL_SPECS']
