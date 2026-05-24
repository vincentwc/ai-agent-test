import json
import os
import pickle, base64
from pathlib import Path

from typing import Sequence, Any

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple, ChannelVersions, CheckpointMetadata, \
    Checkpoint

from app.code_agent.model.qwen import llm_qwen
from app.code_agent.tools.file_tools import file_tools


class FileServer(BaseCheckpointSaver[str]):

    def __init__(self, base_path: str = "/Users/vincent/developEnv/llm/.temp/checkpoint"):
        super().__init__()
        self.base_path = base_path

        os.makedirs(self.base_path, exist_ok=True)

    def _get_checkpoint_path(self, thread_id, checkpoint_id):
        dir_path = os.path.join(self.base_path, thread_id)
        os.makedirs(dir_path, exist_ok=True)

        file_path = os.path.join(dir_path, checkpoint_id + ".json")

        return file_path

    def _serialize_checkpoint(self, data) -> str:
        pickled = pickle.dumps(data)
        return base64.b64encode(pickled).decode("utf-8")

    def _deserialize_checkpoint(self, data):
        decoded = base64.b64decode(data.encode("utf-8"))
        return pickle.loads(decoded)

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Fetch a checkpoint tuple using the given configuration.

        Args:
            config: Configuration specifying which checkpoint to retrieve.

        Returns:
            The requested checkpoint tuple, or `None` if not found.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        # 1. 找到正确的路径
        thread_id = config["configurable"]["thread_id"]
        # checkpoint_id = config["configurable"]["checkpoint_id"]

        # 2. 读取checkpoint文件内容
        dir_path = os.path.join(self.base_path, thread_id)
        checkpoint_files = list(Path(dir_path).glob("*.json"))
        if not checkpoint_files:
            return None
        checkpoint_files.sort(key=lambda x: x.stem, reverse=True)
        latest_checkpoint = checkpoint_files[0]
        checkpoint_id = latest_checkpoint.stem
        checkpoint_file_path = self._get_checkpoint_path(thread_id, checkpoint_id)

        # 3. 对文件进行反序列化
        with open(checkpoint_file_path, "r", encoding="utf-8") as checkpoint_file:
            data = json.load(checkpoint_file)

        checkpoint = self._deserialize_checkpoint(data["checkpoint"])
        metadata = self._deserialize_checkpoint(data["metadata"])

        # 4. 返回checkpoint 对象
        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id,
                }
            },
            metadata=metadata,
            checkpoint=checkpoint,
        )

    def put(
            self,
            config: RunnableConfig,
            checkpoint: Checkpoint,
            metadata: CheckpointMetadata,
            new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Store a checkpoint with its configuration and metadata.

        Args:
            config: Configuration for the checkpoint.
            checkpoint: The checkpoint to store.
            metadata: Additional metadata for the checkpoint.
            new_versions: New channel versions as of this write.

        Returns:
            RunnableConfig: Updated configuration after storing the checkpoint.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        # 1. 生成存储的 json 文件路径
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]

        checkpoint_path = self._get_checkpoint_path(thread_id, checkpoint_id)

        # 2. 将 checkpoint 进行序列化
        checkpoint_data = {
            "checkpoint": self._serialize_checkpoint(checkpoint),
            "metadata": self._serialize_checkpoint(metadata),
        }

        # 3. 将 checkpoint 存储到文件系统
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

        # 4. 生成返回值
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
            self,
            config: RunnableConfig,
            writes: Sequence[tuple[str, Any]],
            task_id: str,
            task_path: str = "",
    ) -> None:
        """Store intermediate writes linked to a checkpoint.

        Args:
            config: Configuration of the related checkpoint.
            writes: List of writes to store.
            task_id: Identifier for the task creating the writes.
            task_path: Path of the task creating the writes.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        # print("put_writes")

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Asynchronously fetch a checkpoint tuple using the given configuration.

        Args:
            config: Configuration specifying which checkpoint to retrieve.

        Returns:
            The requested checkpoint tuple, or `None` if not found.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        return self.get_tuple(config)


    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Asynchronously store a checkpoint with its configuration and metadata.

        Args:
            config: Configuration for the checkpoint.
            checkpoint: The checkpoint to store.
            metadata: Additional metadata for the checkpoint.
            new_versions: New channel versions as of this write.

        Returns:
            RunnableConfig: Updated configuration after storing the checkpoint.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        return self.put(config, checkpoint, metadata, new_versions)


    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Asynchronously store intermediate writes linked to a checkpoint.

        Args:
            config: Configuration of the related checkpoint.
            writes: List of writes to store.
            task_id: Identifier for the task creating the writes.
            task_path: Path of the task creating the writes.

        Raises:
            NotImplementedError: Implement this method in your custom checkpoint saver.
        """
        self.put_writes(config, writes, task_id, task_path)

if __name__ == '__main__':
    memory = FileServer()

    agent = create_agent(
        model=llm_qwen,
        tools=file_tools,
        checkpointer=memory,
        debug=True
    )

    config = RunnableConfig(configurable={"thread_id": 2})

    while True:
        user_input = input("用户:  ")
        if user_input.lower() in ["exit", "quit"]:
            break
        res = agent.invoke(input={"messages": user_input}, config=config)
        print("助理: ", res["messages"][-1].content)
        print()
