p = "src/vulkan/runtime/vk_frame_pacer.c"
s = open(p, newline="").read()
s = s.replace("#include", "#pragma warning(disable: 4189)\n#include", 1)
open(p, "w", newline="").write(s)