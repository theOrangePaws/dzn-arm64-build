import re
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "src" / "microsoft" / "vulkan"

meta_path = root / "dzn_meta.c"
meta = meta_path.read_text()

old_loop = """   if (!pdev->options15.TriangleFanSupported) {
      for (uint32_t i = 0; i < ARRAY_SIZE(device->triangle_fan); i++) {
         result = dzn_meta_triangle_fan_rewrite_index_init(device, i);
         if (result != VK_SUCCESS)
            goto out;
      }
   }
"""
new_loop = """   if (!pdev->options15.TriangleFanSupported) {
      result = dzn_meta_triangle_fan_rewrite_index_init(device, DZN_NO_INDEX);
      if (result != VK_SUCCESS)
         goto out;
   }
"""
if old_loop not in meta:
    sys.exit("dzn_meta.c: triangle fan init loop not found; source differs from expected")
meta = meta.replace(old_loop, new_loop)

getter = """
struct dzn_meta_triangle_fan_rewrite_index *
dzn_meta_get_triangle_fan(struct dzn_device *device,
                          enum dzn_index_type index_type)
{
   static simple_mtx_t lock = SIMPLE_MTX_INITIALIZER;
   struct dzn_meta_triangle_fan_rewrite_index *meta =
      &device->triangle_fan[index_type];

   simple_mtx_lock(&lock);
   if (!meta->pipeline_state)
      dzn_meta_triangle_fan_rewrite_index_init(device, index_type);
   simple_mtx_unlock(&lock);

   return meta;
}

"""
marker = "static const D3D12_SHADER_BYTECODE *\ndzn_meta_blits_get_vs("
if marker not in meta:
    sys.exit("dzn_meta.c: insertion marker not found")
meta = meta.replace(marker, getter + marker, 1)
meta = meta.replace('#include "dzn_private.h"\n',
                    '#include "dzn_private.h"\n#include "util/simple_mtx.h"\n', 1)
meta_path.write_text(meta)

decl = """
struct dzn_meta_triangle_fan_rewrite_index *
dzn_meta_get_triangle_fan(struct dzn_device *device,
                          enum dzn_index_type index_type);
"""
pat = re.compile(r"\b(\w+)->triangle_fan\[([^\]]+)\]")
total = 0
for path in sorted(root.glob("*.c")):
    if path.name == "dzn_meta.c":
        continue
    text = path.read_text()
    new, n = pat.subn(r"(*dzn_meta_get_triangle_fan(\1, \2))", text)
    if n:
        new = new.replace('#include "dzn_private.h"\n',
                          '#include "dzn_private.h"\n' + decl, 1)
        path.write_text(new)
        print(f"{path.name}: patched {n} use(s)")
        total += n
if total == 0:
    sys.exit("no triangle_fan[...] uses found outside dzn_meta.c")
print("ok")

pacer = Path(sys.argv[1]) / "src" / "vulkan" / "runtime" / "vk_frame_pacer.c"
text = pacer.read_text(encoding="utf-8")
if "disable: 4189" not in text:
    new, n = re.subn(r"^#include", "#pragma warning(disable: 4189)\n#include",
                     text, count=1, flags=re.M)
    if n == 0:
        sys.exit("vk_frame_pacer.c: no #include found")
    pacer.write_text(new, encoding="utf-8")
    print("vk_frame_pacer.c: patched C4189")