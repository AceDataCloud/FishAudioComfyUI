# Ace Data Cloud 的 ComfyUI Fish Audio 节点

本包独立对应 [FishAudioDify](https://github.com/AceDataCloud/FishAudioDify)，覆盖快照 `c931c58` 中的 **7 个正式工具定义**和 **3 个固定 model ID**。节点调用 Ace Data Cloud 云 API，无需本地模型或显卡；收费以[当前价格](https://platform.acedata.cloud/models)为准。

[English guide](../README.md)

Registry 版本激活后，在 ComfyUI-Manager 搜索 **Fish Audio**，核对发布者 `acedatacloud` 和包名 **Fish Audio by Ace Data Cloud**，安装并重启。Registry ID 是 `fish-audio`，源码仓库为 `AceDataCloud/FishAudioComfyUI`。源码和上传成功不等于市场可安装。

在**实际 ComfyUI 进程环境**中设置 `ACEDATACLOUD_API_KEY`（也接受 `ACEDATACLOUD_API_TOKEN`），不要写进工作流或仓库。每个 Dify 工具对应一个节点；model/action 选择器覆盖 Dify YAML 的固定选项，其他字段有具名输入框，留空则省略。数组/对象字段在输入框填 JSON 字符串；高级参数也可放进 `parameters_json` JSON 对象，非空具名字段优先。选 `(from JSON/default)` 则使用 JSON 或 API 默认值。任务查询节点可填 `task_id`，批量查询节点可填 `ids_json`。完整字段和 model 列表见[英文主文档](../README.md)。

导入 [01-configure-and-run.json](../examples/01-configure-and-run.json)，先填任务 ID 或 JSON 参数再运行。提交成功不代表媒体完成；用同一个任务 ID 查询至 `succeeded`，把 Ace CDN URL 接到相应 `AUDIO` 节点。收费提交失败时不会自动重试，先查请求记录和价格。删除/归档类动作仍需在 JSON 明确设置 `confirm: true`。详见[隐私说明](PRIVACY.md)。
