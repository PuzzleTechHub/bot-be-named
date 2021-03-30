class Prefix:
	def __init__(self, original: str, prefix: str):
		self.original = str(original)
		self.prefix_str = str(prefix)
		self.prefix_len = len(self.prefix_str)

	def has_prefix(self):
		return self.original[: self.prefix_len] == self.prefix_str

	def add_prefix(self):
		return f"{self.prefix_str}{self.original}"

	def remove_prefix(self):
		return self.original[self.prefix_len :]
