---
name: comfyui
display_name: "ComfyUI Workflows"
build_command: ""
test_command: ""
rotation_size: 4
personas: [implementer, reviewer, tester, security-auditor]
---

# ComfyUI Workflows Review Profile

## Review notes

The reviewed artefacts are ComfyUI workflow graphs saved as JSON, plus any
helper scripts that generate their assets. Expect one of two formats:

- **UI format**: top-level `nodes`, `links`, `groups`, `extra`, `last_node_id`
  and `last_link_id`. Each node has `id`, `type`, `inputs`, `outputs`, `mode`
  and positional `widgets_values`. Each link is
  `[link_id, from_node, from_slot, to_node, to_slot, type]`.
- **API format**: a dictionary of node id to `{class_type, inputs}`, where a
  connected input is `[node_id, output_index]`.

No reviewer can run a workflow. That needs ComfyUI, the custom nodes and the
model weights. So evidence about runtime behaviour is `traced` at best. The
graph itself can be checked mechanically: write a short Python probe that
loads the JSON and checks it. Results from such a probe are `observed`.

`widgets_values` is positional. Its meaning depends on the node class's
declared input order, which lives in ComfyUI or the custom node's source, not
in this repository. A claim that a widget value is wrong for its slot is
`asserted`, unless you read that node's definition. Say which version you read.

The repository's conventions file usually records the target hardware and
backend, such as Apple Silicon/MPS or CUDA with limited VRAM, and nodes known
to be broken on it. Treat that list as binding.

## Implementer Criteria
- Graph integrity:
  - Every link id in `links` appears in both endpoint nodes' `inputs` and `outputs`.
  - Every `inputs[].link` and `outputs[].links` entry exists in `links`.
  - `last_node_id` and `last_link_id` are at least the largest ids in use.
- Types match across each link (for example IMAGE to IMAGE, MASK to MASK,
  LATENT to LATENT). A link of type `*` is legitimate only on reroute and
  primitive nodes.
- Every required input is connected or has a widget value. No dangling
  outputs feed nothing, except preview and save nodes.
- Muted (`mode: 2`) and bypassed (`mode: 4`) nodes are deliberate. Bypassing a
  node passes its first matching input straight through, which can silently
  change what flows downstream. Check that the bypassed path still type-checks
  and means what the workflow's notes say.
- Model, LoRA, ControlNet, upscaler and detector file names in
  `widgets_values` match the repository's model list or setup guide exactly,
  including subfolder and extension.
- Sampler settings suit the stated purpose. Restoration and likeness-preserving
  work needs conservative denoise. Steps and CFG must make sense for the
  checkpoint family (SD1.5, SDXL, Flux). Seed control (`fixed` versus
  `randomize`) must match what the documentation promises.
- Resolution and latent size suit the checkpoint family, and resize nodes keep
  dimensions divisible by 8 (64 for some models).
- The precision and backend constraints from the conventions file are honoured
  (for example no FP8 on MPS, and no node the conventions list as broken).
- Helper scripts are held to ordinary Python tool standards: type hints, pathlib,
  no `shell=True`, specific exceptions, and deterministic output for generated
  assets.

## Reviewer Criteria
- Variants of one workflow (`standard` and `enhanced`, for example) share the
  same logic and differ only where they say they do. When a fix lands in one
  variant, check that it also landed in the other.
- The documentation (README, plan or spec) matches the graph: the node list,
  the models, the inputs the user must supply, and what the output is.
- Mask and compositing logic: the mask polarity (what is white), the grow and
  feather direction, the alpha handling, and the colour space (RGB versus
  RGBA) are consistent through the chain.
- Image batch versus list semantics: nodes that expect one image receive one,
  and the batch size flows through as intended.
- Hard-coded absolute paths, user names or machine-specific folders in widget
  values or scripts make the workflow non-portable between the documented
  platforms.
- Custom-node dependencies are all listed in the setup documentation, with the
  pack that provides each node class.
- `PrimitiveNode` and widget-to-input conversions still point at the input
  they drive. A converted widget whose link was removed leaves a stale value.

## Tester Criteria
- A graph-integrity probe (see Review notes) passes for every workflow file.
  Write one if the repository has none, and report the absence as a coverage
  gap.
- Helper scripts have pytest coverage for the shapes they generate: the
  dimensions, the value ranges and the alpha channel. Their output is
  reproducible, with fixed seeds.
- Edge inputs the workflow will meet in practice are considered:
  - an image with no face detected, so the detector returns an empty SEGS
  - more than one face
  - a portrait-orientation or very small input
  - an input with an alpha channel
  - grayscale input
  A workflow that silently passes the image through unchanged when detection
  fails should say so in its notes.
- Each documented manual test procedure (sample inputs and expected results)
  exists and names the models it was run with.

## Security Auditor Criteria
- Custom nodes run arbitrary Python inside ComfyUI. Every custom-node pack the
  workflows require comes from a named, maintained source, and the setup guide
  says where to install it from. Flag any node pack that has no stated source.
- Model weights: prefer `.safetensors`. `.ckpt`, `.pt` and `.pth` files are
  pickles and can execute code on load. Flag any workflow that requires one
  where a safetensors version exists, and any download link that is not from
  the publisher.
- Embedded metadata: `SaveImage` writes the full workflow and prompt into the
  PNG. For photos of real people, especially minors, check whether outputs
  are shared outside the user's machine and whether that metadata (file
  names, paths, prompts) should be stripped first.
- Input and output file names or paths that reveal client or subject names,
  committed sample images of real people, or EXIF data in committed assets.
- Helper scripts: no network fetch without a pinned source and checksum, and
  no `eval` or `pickle` of downloaded data.

## Project Manager Criteria
- Every workflow in `workflows/` is listed in the README, with its purpose,
  inputs and required models.
- New models or custom nodes are added to the models list and the setup guide.
- Plans and specs for a workflow are updated when the graph diverges from them.
- Platform compatibility notes (primary and secondary machine) are updated when
  a node or model changes.
