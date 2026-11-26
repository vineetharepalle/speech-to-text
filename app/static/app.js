const $ = (id) => document.getElementById(id);
const API = "/api/transcriptions";

let ws, ctx, stream, node, recording = false;

/* ---------------- Live recording ---------------- */

async function startRecording() {
  stream = await navigator.mediaDevices.getUserMedia({
    audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
  });
  ctx = new AudioContext({ sampleRate: 16000 });
  await ctx.audioWorklet.addModule("/static/pcm-worklet.js");

  const source = ctx.createMediaStreamSource(stream);
  node = new AudioWorkletNode(ctx, "pcm-processor");
  const mute = ctx.createGain();
  mute.gain.value = 0;
  source.connect(node);
  node.connect(mute).connect(ctx.destination);

  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws/transcribe`);
  ws.binaryType = "arraybuffer";

  ws.onopen = () => {
    node.port.onmessage = (e) => ws.readyState === WebSocket.OPEN && ws.send(e.data);
    $("status").textContent = "Listening…";
  };
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === "partial") {
      $("committed").textContent = msg.committed;
      $("partial").textContent = msg.partial;
    } else if (msg.type === "final") {
      $("committed").textContent = msg.text;
      $("partial").textContent = "";
      $("status").textContent = msg.id ? "Saved" : "Nothing to save";
      loadRows();
    }
  };
  ws.onerror = () => ($("status").textContent = "Connection error");

  recording = true;
  $("recBtn").textContent = "Stop recording";
  $("recBtn").classList.add("danger");
  $("committed").textContent = "";
  $("partial").textContent = "";
}

function stopRecording() {
  recording = false;
  node?.disconnect();
  stream?.getTracks().forEach((t) => t.stop());
  ctx?.close();
  if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ event: "stop" }));
  $("status").textContent = "Finishing…";
  $("recBtn").textContent = "Start recording";
  $("recBtn").classList.remove("danger");
}

$("recBtn").onclick = async () => {
  try {
    recording ? stopRecording() : await startRecording();
  } catch (err) {
    $("status").textContent = "Mic error: " + err.message;
  }
};

/* ---------------- Dashboard (CRUD) ---------------- */

let editingId = null;

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function loadRows() {
  const q = $("search").value.trim();
  const res = await fetch(`${API}?limit=100${q ? "&q=" + encodeURIComponent(q) : ""}`);
  if (!res.ok) return;
  const items = await res.json();
  $("rows").innerHTML = items
    .map(
      (t) => `
    <tr>
      <td>${esc(t.title)}</td>
      <td class="text">${esc(t.text)}</td>
      <td>${esc(t.language || "-")}</td>
      <td>${Math.round(t.duration_seconds)}s</td>
      <td>${new Date(t.created_at).toLocaleString()}</td>
      <td class="actions">
        <button class="secondary" data-edit="${t.id}">Edit</button>
        <button class="danger" data-del="${t.id}">Delete</button>
      </td>
    </tr>`
    )
    .join("");
}

function openDialog(item) {
  editingId = item ? item.id : null;
  $("dlgTitle").textContent = item ? "Edit transcription" : "New transcription";
  $("fTitle").value = item ? item.title : "";
  $("fText").value = item ? item.text : "";
  $("dlg").showModal();
}

$("rows").onclick = async (e) => {
  const editId = e.target.dataset.edit;
  const delId = e.target.dataset.del;
  if (editId) {
    const res = await fetch(`${API}/${editId}`);
    if (res.ok) openDialog(await res.json());
  } else if (delId && confirm("Delete this transcription?")) {
    await fetch(`${API}/${delId}`, { method: "DELETE" });
    loadRows();
  }
};

$("newBtn").onclick = () => openDialog(null);
$("cancelBtn").onclick = () => $("dlg").close();

$("saveBtn").onclick = async () => {
  const body = { title: $("fTitle").value.trim() || "Untitled", text: $("fText").value };
  const res = await fetch(editingId ? `${API}/${editingId}` : API, {
    method: editingId ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.ok) {
    $("dlg").close();
    loadRows();
  } else {
    alert("Save failed (" + res.status + ")");
  }
};

let timer;
$("search").oninput = () => {
  clearTimeout(timer);
  timer = setTimeout(loadRows, 300);
};

loadRows();
