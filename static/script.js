// --- State Management ---
let currentData = null; // Holds the last successful API json response
let is3D = false;

// --- DOM Elements ---
const form = document.getElementById('calc-form');
const calcTypeSelect = document.getElementById('calc_type');
const receiverParams = document.getElementById('receiver-params');
const batchParams = document.getElementById('batch-params');
const singlePosParams = document.getElementById('single-pos-params');
const singleAngParams = document.getElementById('single-ang-params');
const statusPanel = document.getElementById('status-panel');
const statusText = document.getElementById('status-text');
const progressBar = document.querySelector('.progress-bar');
const downloadBtn = document.getElementById('download-btn');
const plotVariableSelect = document.getElementById('plot-variable');
const toggle3dBtn = document.getElementById('toggle-3d');
const sliceBtn = document.getElementById('btn-slice');
const sliceYInput = document.getElementById('slice-y');
const sliceVariableSelect = document.getElementById('slice-variable');

// --- Tab Logic ---
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        e.target.closest('.tab-btn').classList.add('active');
        document.getElementById(e.target.closest('.tab-btn').dataset.target).classList.remove('hidden');

        // Relayout Plotly if active
        if (currentData) {
            Plotly.Plots.resize(document.getElementById('plotly-map'));
            Plotly.Plots.resize(document.getElementById('plotly-cross'));
        }
    });
});

document.querySelectorAll('.side-tab').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.side-tab').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.side-pane').forEach(c => c.classList.remove('active'));
        e.target.classList.add('active');
        document.getElementById(e.target.dataset.target).classList.add('active');
    });
});

// --- Dynamic Form Inputs ---
calcTypeSelect.addEventListener('change', (e) => {
    const val = e.target.value;
    const isGrid = (val === 'coulomb' || val === 'deformation');

    document.getElementById('grid-params').style.display = isGrid ? 'flex' : 'none';
    document.getElementById('grid-params-y').style.display = isGrid ? 'flex' : 'none';
    document.getElementById('grid-params-inc').style.display = isGrid ? 'flex' : 'none';

    receiverParams.style.display = isGrid ? 'flex' : 'none';
    batchParams.style.display = (val === 'batch') ? 'block' : 'none';
    singlePosParams.style.display = (val === 'single') ? 'flex' : 'none';
    singleAngParams.style.display = (val === 'single') ? 'flex' : 'none';
});

// --- File Drag and Drop ---
const setupFileDrop = (dropAreaId, inputId, isMainInput = false) => {
    const dropArea = document.getElementById(dropAreaId);
    const input = document.getElementById(inputId);
    const msg = dropArea.querySelector('span');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        dropArea.addEventListener(evt, (e) => { e.preventDefault(); e.stopPropagation(); });
    });
    ['dragenter', 'dragover'].forEach(evt => {
        dropArea.addEventListener(evt, () => dropArea.classList.add('dragover'));
    });
    ['dragleave', 'drop'].forEach(evt => {
        dropArea.addEventListener(evt, () => dropArea.classList.remove('dragover'));
    });
    dropArea.addEventListener('drop', (e) => {
        input.files = e.dataTransfer.files;
        msg.textContent = input.files[0].name;
        if (isMainInput) parseAndPlotSources(input.files[0]);
    });
    input.addEventListener('change', () => {
        if (input.files.length > 0) {
            msg.textContent = input.files[0].name;
            if (isMainInput) parseAndPlotSources(input.files[0]);
        }
    });
}
setupFileDrop('file-drop-area', 'file', true);
setupFileDrop('batch-drop-area', 'batch_file', false);

async function parseAndPlotSources(fileObj) {
    if (!fileObj) return;
    setStatus("Parsing source file...", false, true);
    document.getElementById('map-empty').classList.add('hidden'); // allow plotly to render

    const formData = new FormData();
    formData.append('file', fileObj);
    formData.append('calc_type', 'coulomb');
    formData.append('parse_only', 'true');
    formData.append('return_json', 'true');

    try {
        const res = await fetch('/api/calculate', { method: 'POST', body: formData });
        const json = await res.json();

        if (!res.ok || json.error) throw new Error(json.error || "Failed to parse");

        // Temporarily store data just to plot sources
        currentData = json.data;
        // switch to Map tab dynamically if not already on it
        document.querySelector('.tab-btn[data-target="map-view"]').click();

        renderMap(true); // render map in parse-only mode
        setStatus("Source parsed and mapped.", false, false);

    } catch (err) {
        setStatus("Parse Error: " + err.message, true, false);
    }
}

// --- Utility Functions ---
function setStatus(msg, isError = false, showProgress = false) {
    statusPanel.classList.remove('hidden');
    if (isError) statusPanel.classList.add('error');
    else statusPanel.classList.remove('error');
    statusText.textContent = msg;
    if (showProgress) progressBar.classList.remove('hidden');
    else progressBar.classList.add('hidden');
}

// --- Form Submission ---
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    formData.append('return_json', 'true');

    // UI Loading state
    document.getElementById('submit-btn').disabled = true;
    document.querySelector('.spinner').classList.remove('hidden');
    setStatus("Computing Stress in halfspace...", false, true);

    try {
        const res = await fetch('/api/calculate', { method: 'POST', body: formData });
        const json = await res.json();

        if (!res.ok || json.error) {
            throw new Error(json.error || "Unknown Error");
        }

        setStatus("Success", false, false);
        currentData = json.data;

        // Setup download button
        downloadBtn.href = json.download_url;
        downloadBtn.classList.remove('hidden');

        // Remove empty states
        document.getElementById('map-empty').classList.add('hidden');
        document.getElementById('cross-empty').classList.add('hidden');
        document.getElementById('data-empty').classList.add('hidden');

        // Render Visualizations
        populateTable(currentData);
        renderMap();

    } catch (err) {
        setStatus("Error: " + err.message, true, false);
    } finally {
        document.getElementById('submit-btn').disabled = false;
        document.querySelector('.spinner').classList.add('hidden');
    }
});

// --- Table Rendering ---
function populateTable(data) {
    const thead = document.getElementById('table-head-row');
    const tbody = document.getElementById('table-body');
    document.getElementById('results-table').classList.remove('hidden');

    thead.innerHTML = ""; tbody.innerHTML = "";

    // Safety check if data object doesn't actually have arrays (like if parse_only happened)
    if (!data.ux && !data.coulomb && (!data.x || data.x.length === 0)) return;

    const keys = ["x", "y", "z", "ux", "uy", "uz", "sxx", "syy", "szz", "sxy", "sxz", "syz"];
    if (data.coulomb) keys.push("shear", "normal", "coulomb");

    keys.forEach(k => {
        const th = document.createElement('th');
        th.textContent = k.toUpperCase();
        thead.appendChild(th);
    });

    // limit to 100 rows for performance
    const count = data.x ? Math.min(data.x.length, 100) : 0;
    for (let i = 0; i < count; i++) {
        const tr = document.createElement('tr');
        keys.forEach(k => {
            const td = document.createElement('td');
            // Check if key exists and is array before accessing
            if (data[k] && data[k].length > i) {
                td.textContent = Number(data[k][i]).toExponential(3);
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    }
}

// --- Plotly Visualization ---
plotVariableSelect.addEventListener('change', renderMap);
toggle3dBtn.addEventListener('click', () => {
    is3D = !is3D;
    renderMap(window._isParseOnly); // Keep parse-only state if toggling 3D
});

function renderMap(isParseOnly = false) {
    if (!currentData) return;
    window._isParseOnly = isParseOnly;

    const v = plotVariableSelect.value;
    const vals = currentData[v] || currentData.ux; // fallback

    // Safety check arrays exist before rendering
    const hasData = currentData.x && currentData.y && currentData.x.length > 0;
    const isGrid = hasData && currentData.x.length > 50 && (new Set(currentData.x).size > 1 && new Set(currentData.y).size > 1);

    const traces = [];

    if (!isParseOnly && hasData) {
        if (isGrid && !is3D) {
            // Assume X and Y are ordered meshgrid. Plotly Contour needs 1D arrays if we use mesh=true, but 2D is better.
            // Actually, just passing x, y, z to contour with contour smoothing works.
            traces.push({
                x: currentData.x,
                y: currentData.y,
                z: vals,
                type: 'contour',
                colorscale: 'Jet',
                colorbar: { title: v.toUpperCase(), titleside: 'right' },
                contours: { coloring: 'heatmap' }
            });
        } else {
            // Scatter / Scatter3D
            traces.push({
                x: currentData.x,
                y: currentData.y,
                z: is3D ? currentData.z : vals, // if 3D, z is depth.
                mode: 'markers',
                marker: {
                    color: vals,
                    colorscale: 'Jet',
                    size: 6,
                    colorbar: { title: v.toUpperCase() },
                    showscale: true
                },
                type: is3D ? 'scatter3d' : 'scatter'
            });
        }
    }

    // Add faults
    if (currentData.faults) {
        currentData.faults.forEach((f, idx) => {
            // f: xs, ys, xf, yf, latslip, dipslip, dip, top, bottom
            if (is3D) {
                traces.push({
                    x: [f[0], f[2]],
                    y: [f[1], f[3]],
                    z: [-f[7], -f[8]], // Top to bottom depth
                    mode: 'lines',
                    line: { color: 'white', width: 4 },
                    name: `Fault ${idx + 1}`,
                    type: 'scatter3d'
                });
            } else {
                traces.push({
                    x: [f[0], f[2]],
                    y: [f[1], f[3]],
                    mode: 'lines',
                    line: { color: 'white', width: 2 },
                    name: `Fault ${idx + 1}`,
                    type: 'scatter'
                });
            }
        });
    }

    const layout = {
        title: `Observation Map: ${v.toUpperCase()}`,
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#f0f0f5' },
        margin: { l: 50, r: 50, t: 50, b: 50 },
        scene: is3D ? {
            xaxis: { title: 'X (km)' },
            yaxis: { title: 'Y (km)' },
            zaxis: { title: 'Depth (km)' }
        } : {},
        xaxis: is3D ? undefined : { title: 'X (km)' },
        yaxis: is3D ? undefined : { title: 'Y (km)' }
    };

    Plotly.newPlot('plotly-map', traces, layout, { responsive: true });
}

// --- Cross Section ---
sliceBtn.addEventListener('click', renderCrossSection);
sliceVariableSelect.addEventListener('change', renderCrossSection);

function renderCrossSection() {
    if (!currentData) return;
    const yTarget = parseFloat(sliceYInput.value);
    const v = sliceVariableSelect.value;
    const vals = currentData[v] || currentData.ux;

    // Tolerance for floating point matching
    const tol = 0.5;

    const sliceX = [];
    const sliceV = [];

    for (let i = 0; i < currentData.x.length; i++) {
        if (Math.abs(currentData.y[i] - yTarget) < tol) {
            sliceX.push(currentData.x[i]);
            sliceV.push(vals[i]);
        }
    }

    if (sliceX.length === 0) {
        alert("No data found near Y=" + yTarget);
        return;
    }

    // Sort array by X
    const zipped = sliceX.map((x, i) => [x, sliceV[i]]).sort((a, b) => a[0] - b[0]);
    const sx = zipped.map(t => t[0]);
    const sv = zipped.map(t => t[1]);

    const trace = {
        x: sx,
        y: sv,
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#ff7eb3', width: 2 },
        marker: { size: 6 }
    };

    const layout = {
        title: `Cross Section at Y ≈ ${yTarget} km`,
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#f0f0f5' },
        xaxis: { title: 'Distance X (km)', gridcolor: 'rgba(255,255,255,0.1)' },
        yaxis: { title: v.toUpperCase(), gridcolor: 'rgba(255,255,255,0.1)' }
    };

    Plotly.newPlot('plotly-cross', [trace], layout, { responsive: true });
}

// --- Creator Form Logic ---
const faultsContainer = document.getElementById('faults-container');
const btnAddFault = document.getElementById('btn-add-fault');
const creatorForm = document.getElementById('creator-form');
let faultCount = 0;

function createFaultCard() {
    faultCount++;
    const card = document.createElement('div');
    card.className = 'fault-card';
    card.id = `fault-card-${faultCount}`;

    card.innerHTML = `
        <div class="fault-card-header">
            <strong>Fault ${faultCount}</strong>
            <button type="button" class="btn-icon btn-danger btn-remove-fault" data-target="${card.id}">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        <div class="form-row">
            <div class="form-group"><label>X-Start</label><input type="number" step="0.01" class="f-xs" value="-10" required></div>
            <div class="form-group"><label>Y-Start</label><input type="number" step="0.01" class="f-ys" value="-10" required></div>
            <div class="form-group"><label>X-Fin</label><input type="number" step="0.01" class="f-xf" value="10" required></div>
            <div class="form-group"><label>Y-Fin</label><input type="number" step="0.01" class="f-yf" value="10" required></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Rake (°)</label><input type="number" step="0.1" class="f-rake" value="90" required></div>
            <div class="form-group"><label>Net Slip (m)</label><input type="number" step="0.01" class="f-slip" value="1.0" required></div>
            <div class="form-group"><label>Dip (°)</label><input type="number" step="0.1" class="f-dip" value="45" required></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Top Depth (km)</label><input type="number" step="0.1" class="f-top" value="0.0" required></div>
            <div class="form-group"><label>Bot Depth (km)</label><input type="number" step="0.1" class="f-bot" value="15.0" required></div>
        </div>
    `;

    card.querySelector('.btn-remove-fault').addEventListener('click', (e) => {
        const id = e.target.closest('button').dataset.target;
        document.getElementById(id).remove();
    });

    faultsContainer.appendChild(card);
}

btnAddFault.addEventListener('click', createFaultCard);

// Add initial fault
createFaultCard();

creatorForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Construct .inp file string
    const pr1 = document.getElementById('c_pr1').value;
    const fric = document.getElementById('c_fric').value;
    const depth = document.getElementById('c_depth').value;
    const young = document.getElementById('c_young').value;

    let inpStr = `Created via Web UI\n`;
    inpStr += `#reg1=  0  #reg2=  0  #fixed= 225  sym=  1\n`;
    inpStr += ` PR1=       ${pr1}     PR2=       ${pr1}   DEPTH=       ${depth}\n`;
    inpStr += `  E1=      ${Number(young).toExponential(3)}   E2=      ${Number(young).toExponential(3)}\n`;
    inpStr += `XSYM=       .000     YSYM=       .000\n`;
    inpStr += `FRIC=          ${fric}\n`;
    inpStr += `S1DR=         19.000 S1DP=         -0.010 S1IN=        100.000 S1GD=          0.000\n`;
    inpStr += `S2DR=         89.990 S2DP=         89.990 S2IN=         30.000 S2GD=          0.000\n`;
    inpStr += `S3DR=        109.000 S3DP=         -0.010 S3IN=          0.000 S3GD=          0.000\n\n`;

    inpStr += `  #   X-start    Y-start     X-fin      Y-fin   Kode  rake     netslip   dip angle     top      bot\n`;
    inpStr += `xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n`;

    const cards = document.querySelectorAll('.fault-card');
    cards.forEach((c, idx) => {
        const xs = parseFloat(c.querySelector('.f-xs').value);
        const ys = parseFloat(c.querySelector('.f-ys').value);
        const xf = parseFloat(c.querySelector('.f-xf').value);
        const yf = parseFloat(c.querySelector('.f-yf').value);
        const rake = parseFloat(c.querySelector('.f-rake').value);
        const slip = parseFloat(c.querySelector('.f-slip').value);
        const dip = parseFloat(c.querySelector('.f-dip').value);
        const top = parseFloat(c.querySelector('.f-top').value);
        const bot = parseFloat(c.querySelector('.f-bot').value);

        inpStr += `  1 ${xs.toFixed(4).padStart(10)} ${ys.toFixed(4).padStart(10)} ${xf.toFixed(4).padStart(10)} ${yf.toFixed(4).padStart(10)} 100 ` +
            `${rake.toFixed(4).padStart(10)} ${slip.toFixed(4).padStart(10)} ${dip.toFixed(4).padStart(10)} ` +
            `${top.toFixed(4).padStart(10)} ${bot.toFixed(4).padStart(10)} FFM${idx}\n`;
    });

    inpStr += `\n     Grid Parameters\n`;
    inpStr += `1 ----------------------------  Start-x =    ${parseFloat(document.getElementById('c_xs').value).toFixed(5).padStart(12)}\n`;
    inpStr += `2 ----------------------------  Start-y =    ${parseFloat(document.getElementById('c_ys').value).toFixed(5).padStart(12)}\n`;
    inpStr += `3 --------------------------   Finish-x =    ${parseFloat(document.getElementById('c_xf').value).toFixed(5).padStart(12)}\n`;
    inpStr += `4 --------------------------   Finish-y =    ${parseFloat(document.getElementById('c_yf').value).toFixed(5).padStart(12)}\n`;
    inpStr += `5 -----------------------   x-increment =    ${parseFloat(document.getElementById('c_xinc').value).toFixed(5).padStart(12)}\n`;
    inpStr += `6 -----------------------   y-increment =    ${parseFloat(document.getElementById('c_yinc').value).toFixed(5).padStart(12)}\n`;

    // Create File object
    const blob = new Blob([inpStr], { type: 'text/plain' });
    const file = new File([blob], "created_source.inp", { type: 'text/plain' });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('calc_type', 'coulomb');
    formData.append('receiver_strike', '0');
    formData.append('receiver_dip', '90');
    formData.append('receiver_rake', '0'); // Grid calculations use optimal receiver planes anyway
    formData.append('return_json', 'true');

    document.getElementById('btn-create-submit').disabled = true;
    setStatus("Computing Stress in halfspace...", false, true);

    try {
        const res = await fetch('/api/calculate', { method: 'POST', body: formData });
        const json = await res.json();

        if (!res.ok || json.error) {
            throw new Error(json.error || "Unknown Error");
        }

        setStatus("Success", false, false);
        currentData = json.data;
        downloadBtn.href = json.download_url;
        downloadBtn.classList.remove('hidden');

        document.getElementById('map-empty').classList.add('hidden');
        document.getElementById('cross-empty').classList.add('hidden');
        document.getElementById('data-empty').classList.add('hidden');

        populateTable(currentData);
        renderMap();

        // Switch tab to map view automatically
        document.querySelector('.tab-btn[data-target="map-view"]').click();

    } catch (err) {
        setStatus("Error: " + err.message, true, false);
    } finally {
        document.getElementById('btn-create-submit').disabled = false;
        progressBar.classList.add('hidden');
    }
});
