class Experiment {
    constructor(bloodData, electricData){
        this.data = {
            bloodData: this.parseBlood(bloodData),
            electricData: this.parseElectric(electricData),
        }
    }
    parseBlood(raw_data){
        const data = [];
        const lines = raw_data.split(/\r\n|\n/);
        let i = 0; while (lines[i] != "No: 	Hour 	Min 	Sec 	F1 ") i++;
        for (i += 1; i < lines.length - 1; i++) data.push(lines[i].split("\t")[4]);
        return data
    }
    parseElectric(raw_data){
        const data = [];
        const lines = raw_data.split(/\r\n|\n/);
        let i = 0; while (lines[i] != "No,Time (hr:min:sec),LeftLU,Event messages") i++;
        for (i += 1; lines[i]; i++) data.push(lines[i].split(",")[2]);
        return data
    }
}
class FrontEndManager {
    constructor() {
        this.raw_data = {blood: null, electric: null};
        this.experiment = null;
        this.chart = null; 

        this.divs = { div1: this.getContainerElements('data-input-1'),
                          div2: this.getContainerElements('data-input-2')};

        this.initEventListeners();
    }
    readFromInput(event, key) {
        const reader = new FileReader();
        reader.onload = () => { this.raw_data[key] = reader.result; };
        reader.readAsText(event.target.files[0]);
    }
    createExperiment(){ this.experiment = new Experiment(this.fileContents['blood'], this.fileContents['electric']); }
    getContainerElements(containerId) {
        const container = document.getElementById(containerId);
        return {
            container,
            file: container.querySelector('.file-select'),
            start: container.querySelector('.start-time'),
            end: container.querySelector('.end-time'),
            min: container.querySelector('.graph-min'),
            max: container.querySelector('.graph-max')
        };}

    initEventListeners(){
        this.divs.div1.file.addEventListener('change', () => this.findTimeRange('div1'));
        this.divs.div1.container.querySelector('.find-local-range').addEventListener('click', ()=> this.findLocalRange('div1'));
        this.divs.div2.file.addEventListener('change', () => this.findTimeRange('div2'));
        this.divs.div2.container.querySelector('.find-local-range').addEventListener('click', ()=> this.findLocalRange('div2'));
    }
    getDivData(divId) {
        const div = this.divs[divId];
        const fileKey = div.file.value;
        const data = this.experiment.data[fileKey];
        return [data, div];
    }
    findTimeRange(divId) {
        const [data, div] = this.getDivData(divId);
        div.start.value = 0;
        div.end.value = data.length - 1;
    }
    findLocalRange(divId){
        const [data, div] = this.getDivData(divId);
        const local_data = data.slice(div.start.value, div.end.value);
        div.min.value = Math.min(...local_data);
        div.max.value = Math.max(...local_data);
    }    
    plotGraph(){
        const [data1, div1] = this.getDivData('div1');
        const [data2, div2] = this.getDivData('div2');
        const graph_start_time = Math.min(div1.start.value, div2.start.value)
        const graph_end_time = Math.max(div1.end.value, div2.end.value)
        const labels = []
        for (let i = graph_start_time; i < graph_end_time; i++){labels.push(i)}

        const ctx = document.getElementById('combined-chart').getContext('2d');

        if (this.chart) {
            this.chart.data.labels = labels;
            this.chart.data.datasets[0].data = data1.slice(div1.start.value, div1.end.value);
            this.chart.data.datasets[1].data = data2.slice(div2.start.value, div2.end.value);
            
            // Update scales
            this.chart.options.scales.yBlood.min = div1.min.value;
            this.chart.options.scales.yBlood.max = div1.max.value;
            this.chart.options.scales.yElectric.min = div2.min.value;
            this.chart.options.scales.yElectric.max = div2.max.value;
            this.chart.update();
        } 
        else {
            this.chart = new Chart(ctx, { type: 'line', data: { labels: labels, datasets: [
                { label: 'Blood Flow', data: data1, borderColor: 'red', fill: false, yAxisID: 'yBlood', pointRadius: 0 },
                { label: 'Electric Flow', data: data2, borderColor: 'blue', fill: false, yAxisID: 'yElectric', pointRadius: 0} ]},
                options: { responsive: false, maintainAspectRatio: false, scales: {
                    x: { title: { display: true, text: 'Time'}},
                    yBlood: { type: 'linear', position: 'left', text: 'Blood flow scale', min: div1.min.value, max: div1.max.value, ticks: {callback: function(value) { return value; }}},
                    yElectric: { type: 'linear', position: 'right', text: 'Electric flow scale', min: div2.min.value, max: div2.max.value, ticks: {callback: function(value) { return value; }}}
                }}});
        }
    }
}


const manager = new FrontEndManager();
document.getElementById("blood-file-input").addEventListener('change', (e) => manager.readFromInput(e, 'blood'));
document.getElementById("electric-file-input").addEventListener('change', (e) => manager.readFromInput(e, 'electric'));
document.getElementById("submit-file-input").addEventListener('click', () => manager.createExperiment());
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
  const canvasDiv = document.getElementById('canvas-div');
  const canvas = document.getElementById('combined-chart');
  canvas.width = canvasDiv.clientWidth;
  canvas.height = canvasDiv.clientHeight;
}

resizeCanvas();
window.addEventListener('resize', resizeCanvas);