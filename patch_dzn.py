import glob
p = glob.glob("**/src/vulkan/runtime/vk_frame_pacer.c", recursive=True)[0]
s = open(p, encoding="utf-8", newline="").read()
s = s.replace("#include", "#pragma warning(disable: 4189)\n#include", 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("patched", p)