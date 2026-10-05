"""Copy into providers.py and register after implementing your backend."""
class ExampleProvider:
    name = 'example'
    def __init__(self, root):
        self.model_id = 'replace-with-real-model-id'
    def generate(self, messages, *, max_tokens=100, temperature=.35):
        raise NotImplementedError('Implement text generation and add a mocked contract test.')
