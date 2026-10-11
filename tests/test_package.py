"""Contract snapshot, ComfyUI registration, and paid retry boundary."""

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('parity_comfy', ROOT / '__init__.py',
    submodule_search_locations=[str(ROOT)])
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
nodes = sys.modules['parity_comfy.nodes']
client_module = sys.modules['parity_comfy.client']
Client = client_module.AceDataFishClient
EXPECTED_TOOLS = ['fish_create_model', 'fish_create_voice', 'fish_generate_audio', 'fish_get_voice', 'fish_search_voices', 'fish_task_retrieve', 'fish_tasks_retrieve_batch']
EXPECTED_MODELS = ['s1', 's2-pro', 's2.1-pro']


class ParityTests(unittest.TestCase):
    def test_every_dify_tool_and_model_choice_is_exposed(self):
        self.assertEqual(set(nodes.TOOL_SPECS), set(EXPECTED_TOOLS))
        actual = {model for spec in nodes.TOOL_SPECS.values() for model in spec['models']}
        self.assertEqual(actual, set(EXPECTED_MODELS))
        self.assertEqual(len(nodes.NODE_CLASS_MAPPINGS), len(EXPECTED_TOOLS) + len(nodes.MEDIA_TYPES))

    def test_published_contract_examples_prepare_without_network(self):
        fixtures = json.loads((ROOT / 'tests/contract-examples.json').read_text())
        client = Client('test-key')
        for example in fixtures:
            with self.subTest(example=example['name']):
                inputs = dict(example['inputs'])
                endpoint = client_module.ENDPOINTS[example['tool']]
                if endpoint.get('destructive') or inputs.get('action') in {'delete', 'archive'}:
                    inputs['confirm'] = True
                method, path, body, *_ = client.prepare(example['tool'], inputs)
                self.assertEqual((method, path), (example['method'], example['path']))
                for key, value in example.get('body', {}).items():
                    self.assertEqual(body.get(key), value)

    def test_pending_task_id_is_visible_without_claiming_media(self):
        tool = EXPECTED_TOOLS[0]
        node = next(cls for cls in nodes.NODE_CLASS_MAPPINGS.values()
                    if getattr(cls, 'TOOL', None) == tool)()
        pending = {'status': 'pending', 'task_id': 'task-123', 'trace_id': 'trace-123',
                   'media_urls': [], 'data': {}, 'result': {}}
        with patch.object(nodes, '_credential', return_value='test-key'):
            with patch.object(Client, 'invoke', return_value=pending):
                result = node.run('{}')
        self.assertEqual(result['result'][:4], ('pending', 'task-123', '[]', ''))
        self.assertIn('task-123', ' '.join(result['ui']['text']))

    def test_invalid_json_stops_before_auth_or_network(self):
        tool = EXPECTED_TOOLS[0]
        node = next(cls for cls in nodes.NODE_CLASS_MAPPINGS.values()
                    if getattr(cls, 'TOOL', None) == tool)()
        with patch.object(nodes, '_credential') as credential:
            with self.assertRaises(ValueError):
                node.run('[]')
        credential.assert_not_called()

    def test_paid_request_connection_error_is_not_retried(self):
        client = Client('test-key')
        with patch.object(client_module.requests, 'request', side_effect=client_module.requests.Timeout()) as request:
            with self.assertRaises(Exception):
                client._request('POST', '/example', {}, read_only=False)
        request.assert_called_once()


if __name__ == '__main__':
    unittest.main()
