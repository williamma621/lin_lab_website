class bflowData {
    constructor(text){
        const lines = text.split(/\r\n|\n/);
        this.data = [];
        let i = 0; while (lines[i] != "No: 	Hour 	Min 	Sec 	F1 ") i++;
        for (i += 1; i < lines.length - 1; i++) this.data.push(lines[i].split("\t")[4]);
        this.start = 0 
        this.end = this.data.length - 1
    }
}
class eflowData {
    constructor(text){
        const lines = text.split(/\r\n|\n/);
        this.data = [];
        let i = 0; while (lines[i] != "No,Time (hr:min:sec),LeftLU,Event messages") i++;
        for (i += 1; lines[i]; i++) this.data.push(lines[i].split(",")[2]);
        this.start = 0 
        this.end = this.data.length - 1
        this.min = Math.min(...this.data)
        this.max = Math.max(...this.data)
    }
}
class FileDataManager {
    constructor() {
        this.bflow = null;
        this.eflow = null;
        this.chart = null; 

        
        this.b_start = document.querySelector('.b-flow-inputs .start-time');
        this.b_end = document.querySelector('.b-flow-inputs .end-time');
        this.b_min = document.querySelector('.b-flow-inputs .graph-min');
        this.b_max = document.querySelector('.b-flow-inputs .graph-max');

        this.e_start = document.querySelector('.e-flow-inputs .start-time');
        this.e_end = document.querySelector('.e-flow-inputs .end-time');
        this.e_min = document.querySelector('.e-flow-inputs .graph-min');
        this.e_max = document.querySelector('.e-flow-inputs .graph-max');

    }

    readFromInput(event, key) {
        const reader = new FileReader();
        reader.onload = () => { 
            if (key == 'bflow') {
                this.bflow = new bflowData(reader.result);
                this.b_start.value = this.bflow.start;
                this.b_end.value = this.bflow.end;
            }
            if (key == 'eflow') {
                this.eflow = new eflowData(reader.result);
                this.e_start.value = this.eflow.start;
                this.e_end.value = this.eflow.end;
            }
        };
        reader.readAsText(event.target.files[0]);
    }
    localRange(key){
        if (key == "bflow"){
            const local_data = this.bflow.data.slice(this.b_start.value, this.b_end.value)
            this.b_min.value = Math.min(...local_data)
            this.b_max.value = Math.max(...local_data)
        }
        if (key == "eflow"){
            const local_data = this.eflow.data.slice(this.e_start.value, this.e_end.value)
            this.e_min.value = parseFloat(Math.min(...local_data))
            this.e_max.value = parseFloat(Math.max(...local_data))
        }
    }
    plotGraph(){
        const bloodData = manager.bflow ? manager.bflow.data : [];
        const bflowParameters = {
            start: document.querySelector('.b-flow-inputs .start-time').value,
              end: document.querySelector('.b-flow-inputs .end-time').value,
              min: document.querySelector('.b-flow-inputs .graph-min').value,
              max: document.querySelector('.b-flow-inputs .graph-max').value,

        }
        const electricData = manager.eflow ? manager.eflow.data : [];
        const eflowParameters = {
            start: document.querySelector('.e-flow-inputs .start-time').value,
              end: document.querySelector('.e-flow-inputs .end-time').value,
              min: document.querySelector('.e-flow-inputs .graph-min').value,
              max: document.querySelector('.e-flow-inputs .graph-max').value,
        }

        const graph_start_time = Math.min(bflowParameters['start'], eflowParameters['start'])
        const graph_end_time = Math.max(bflowParameters['end'], eflowParameters['end'])

        const labels = []
        for (let i = graph_start_time; i < graph_end_time; i++){labels.push(i)}

        const ctx = document.getElementById('combined-chart').getContext('2d');
        if (this.chart) {
            this.chart.data.labels = labels;
            this.chart.data.datasets[0].data = bloodData.slice(labels[graph_start_time], labels[graph_end_time]);
            this.chart.data.datasets[1].data = electricData.slice(labels[graph_start_time], labels[graph_end_time]);
            
            // Update scales
            this.chart.options.scales.yBlood.min = bflowParameters['min'];
            this.chart.options.scales.yBlood.max = bflowParameters['max'];
            this.chart.options.scales.yElectric.min = eflowParameters['min'];
            this.chart.options.scales.yElectric.max = eflowParameters['max'];
            
            this.chart.update();
        } 
        else {
            this.chart = new Chart(ctx, { type: 'line', data: { labels: labels, datasets: [
                { label: 'Blood Flow', data: bloodData, borderColor: 'red', fill: false, yAxisID: 'yBlood', pointRadius: 0 },
                { label: 'Electric Flow', data: electricData, borderColor: 'blue', fill: false, yAxisID: 'yElectric', pointRadius: 0} ]},
                options: { responsive: false, maintainAspectRatio: false, scales: {
                    x: { title: { display: true, text: 'Time'}},
                    yBlood: { type: 'linear', position: 'left', text: 'Blood flow scale', min: bflowParameters['min'], max: bflowParameters['max'], ticks: {callback: function(value) { return value; }}},
                    yElectric: { type: 'linear', position: 'right', text: 'Electric flow scale', min: eflowParameters['min'], max: eflowParameters['max'], ticks: {callback: function(value) { return value; }}}
                }}});
        }
    }
}


const manager = new FileDataManager();
document.getElementById("b-flow-file").addEventListener('change', (e) => manager.readFromInput(e, 'bflow'));
document.getElementById("e-flow-file").addEventListener('change', (e) => manager.readFromInput(e, 'eflow'));
document.getElementById("find-bflow-range").addEventListener('click',() => manager.localRange('bflow'))
document.getElementById("find-eflow-range").addEventListener('click',() => manager.localRange('eflow'))
document.getElementById("generate-graph").addEventListener('click', () => manager.plotGraph());


function calculate_basic_stats(data){
    const lines = [];

    for (let i = 45; i < 2049; i++){
        const row = data[i].split("\t");
        const timestamp = `${row[1]}:${row[2]}:${row[3]}`;
        lines.push(parseFloat(row[4]));
    }
    part1_begin = 0
    part1_end = 120
    part1_slice = lines.slice(part1_begin, part1_end)
    part1_mean = ss.mean(part1_slice)
    part1_sd = ss.standardDeviation(part1_slice)

    part2_begin = 121
    part2_end = 240
    part2_slice = lines.slice(part2_begin, part2_end)
    part2_mean = ss.mean(part2_slice)
    part2_sd = ss.standardDeviation(part2_slice)

    const tTestResult = ss.tTestTwoSample(part1_slice, part2_slice);
    console.log("Part1 Mean:", part1_mean);
    console.log("Part1 SD:", part1_sd);
    console.log("Part2 Mean:", part2_mean);
    console.log("Part2 SD:", part2_sd);

    console.log("t-stats: ", tTestResult);
}


function resizeCanvas() {
  const canvas_div = document.getElementById('canvas-div');
document.getElementById('combined-chart').width = document.getElementById('canvas-div').clientWidth;
document.getElementById('combined-chart').height = document.getElementById('canvas-div').clientHeight;  

  canvas.width = canvasDiv.clientWidth;
  canvas.height = canvasDiv.clientHeight;
}

resizeCanvas();
window.addEventListener('resize', resizeCanvas);