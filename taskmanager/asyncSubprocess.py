import asyncio

class AsyncSubprocess:
    def __init__(self, command, encoding='utf-8'):
        self.command = command
        self.encoding = encoding
        self.process = None

    async def _read_stream(self, stream, tag, callback=None):
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded_line = line.decode(self.encoding).strip()
            if callback:
                await callback(tag, decoded_line)
            else:
                print(f'[{tag}] {decoded_line}')

    async def run(self, stdout_callback=None, stderr_callback=None):
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 并发读取 stdout 和 stderr
        await asyncio.gather(
            self._read_stream(self.process.stdout, 'stdout', stdout_callback),
            self._read_stream(self.process.stderr, 'stderr', stderr_callback)
        )
        
        return_code = await self.process.wait()
        return return_code

# 使用示例
async def custom_callback(tag, line, file_handler=None):
    print(f'[{tag}] {line}')

async def main():
    command = ['ping', '-c', '4', 'baidu.com']
    tool = AsyncSubprocess(command)
    await tool.run(stdout_callback=custom_callback, stderr_callback=custom_callback)

if __name__ == '__main__':
    asyncio.run(main())