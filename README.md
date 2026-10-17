# Fish Audio for ComfyUI by Ace Data Cloud

Use the current [FishAudioDify](https://github.com/AceDataCloud/FishAudioDify) tool contracts as independent ComfyUI nodes. This package exposes all **7 Dify tool definitions** and **3 fixed model IDs** from source snapshot `c931c58`. It calls the hosted Ace Data Cloud API; no local model or GPU is needed. Paid actions consume Credits at the [current service price](https://platform.acedata.cloud/models?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=fishaudiocomfyui_readme_en_pricing).

[简体中文](docs/README.zh-CN.md) · [Ace Data Cloud](https://platform.acedata.cloud?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=fishaudiocomfyui_readme_en_home) · [Issues](https://github.com/AceDataCloud/FishAudioComfyUI/issues)

## Install

Open **Manager → Custom Nodes Manager** and search **Ace Data Cloud**. Select **Fish Audio by Ace Data Cloud**, confirm publisher **acedatacloud** and source repository [`AceDataCloud/FishAudioComfyUI`](https://github.com/AceDataCloud/FishAudioComfyUI), then click **Install**. In **Select Version**, explicitly select the approved Registry stable release **0.1.0**. The normal dialog may initially highlight **nightly**; do not accept it for this stable-release tutorial. Keep dependency installation enabled. After **Restart Required**, restart ComfyUI and refresh the browser. Registry ID: `fish-audio`.

This Registry stable installation was verified on **2026-10-16 with original ComfyUI 0.41.0 on Linux CPU**. That test did not submit a generation or chat request. Newer host versions and each paid action require their own checks; model availability and price remain subject to the current service rules.

For local source testing, clone this repository into `ComfyUI/custom_nodes/FishAudioComfyUI` and run `python -m pip install -r requirements.txt` in ComfyUI's environment, then restart. Native media loaders require ComfyUI 0.39.0 or newer. This package uses ComfyUI's existing image/audio/video libraries for decoding.

## Key and tool inputs

1. Sign in to [Ace Data Cloud → Applications](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=fishaudiocomfyui_readme_en_api_key). If your account has no General application, choose **Initialize General Application**.
2. Open **General application** and check access to the service used by this package. A service-specific application key is limited to that service. Copy an existing API key, or choose **Manage Keys → Create** for a separate key named `ComfyUI`.
3. Copy only the token string, without `Bearer ` or quotation marks. A platform management token is not the API key these nodes use. If you enable **Allowed APIs**, include every submission and task-query path used by your workflow. Check current pricing and available Credits before a paid action.

Set `ACEDATACLOUD_API_KEY` (or `ACEDATACLOUD_API_TOKEN`) in the **ComfyUI process environment** and restart. Keep the key out of workflow JSON, screenshots, issues, and the repository.

Each Dify tool has its own node. The model and action selectors expose every fixed choice in the source YAML. Other fields appear as named text or confirmation widgets; leave one empty to omit it. `parameters_json` accepts the same API fields as an advanced JSON object. A nonempty widget overrides the matching JSON field; `(from JSON/default)` keeps a model/action supplied by JSON or the API default. Arrays and objects can be entered as JSON strings in their named widgets. Task lookup nodes also offer `task_id` and `wait_seconds`; batch lookup nodes offer `ids_json`. Contract validation happens before a request. Paid submissions are never retried after a connection failure; preserve an accepted task ID and inspect request history before paying again.

| Dify tool | Required fields in JSON | Model choices | Action choices |
| --- | --- | --- | --- |
| `fish_create_model` | `title`, `voices` | — | — |
| `fish_create_voice` | `voice_url` | — | — |
| `fish_generate_audio` | `text` | `s1`, `s2-pro`, `s2.1-pro` | — |
| `fish_get_voice` | `id` | — | — |
| `fish_search_voices` | — | — | — |
| `fish_task_retrieve` | `task_id` | — | — |
| `fish_tasks_retrieve_batch` | `ids` | — | — |

Import [01-configure-and-run.json](examples/01-configure-and-run.json) with **File → Open**, fill its placeholder task ID or JSON parameters, then run. The example is a configuration template; it does not submit a paid request by itself. Query the same task ID until `status` is `succeeded`. The node returns status, task ID, all media URLs as JSON, first media URL, normalized result JSON, and trace ID. Connect a completed Ace CDN URL to the provided `AUDIO` loader where applicable.

Check current service pricing before a paid run. Read-only task queries and media downloads should not generate a new paid task. Destructive Dify actions still require an explicit `confirm: true` in JSON. See [privacy notes](docs/PRIVACY.md).

## Development

```bash
python -m unittest discover -s tests -v
python -m py_compile __init__.py client.py api_contracts.py nodes.py
```

`pyproject.toml` declares short Registry ID `fish-audio`, publisher `acedatacloud`, and a 400×400 proportional resize of the [canonical Ace logo](https://cdn.acedata.cloud/assets/logo.png).
