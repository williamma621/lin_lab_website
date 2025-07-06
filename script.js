class bflowData {
    constructor(text){
        const lines = text.split(/\r\n|\n/);
        this.data = [];
        let i = 0; while (lines[i] != "No: 	Hour 	Min 	Sec 	F1 ") i++;
        for (i += 1; i < lines.length - 1; i++) this.data.push(lines[i].split("\t")[4])
    }
}
class eflowData {
    constructor(text){
        const lines = text.split(/\r\n|\n/);
        this.data = [];
        let i = 0; while (lines[i] != "No,Time (hr:min:sec),LeftLU,Event messages") i++;
        for (i += 1; lines[i]; i++) this.data.push(lines[i].split(",")[2])
    }
}
class FileDataManager {
    constructor() {
        this.eflow = null;
        this.bflow = null;
    }

    readFromInput(event, key) {
        const reader = new FileReader();
        reader.onload = () => { 
            if (key == 'bflow') this.bflow = new bflowData(reader.result); 
            if (key == 'eflow') this.eflow = new eflowData(reader.result);
            b_flow_start.value = 0;
        };
        reader.readAsText(event.target.files[0]);
    }

    plotGraph(){

    }
}



let b_flow_file = document.getElementById("b-flow-file")
let b_flow_start = document.getElementById("b-flow-start")
let e_flow_file = document.getElementById("e-flow-file")
let button1 = document.getElementById("generate-graph")

const manager = new FileDataManager();
b_flow_file.addEventListener('change', (e) => manager.readFromInput(e, 'bflow'));
e_flow_file.addEventListener('change', (e) => manager.readFromInput(e, 'eflow'));
button1.addEventListener('click', plotGraph);



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

function plotGraph(){

const bloodData = manager.bflow.data
const electricData = manager.eflow.data
const ctx = document.getElementById('combined-chart').getContext('2d');
const labels = []
for (let i = 0; i< 2099; i++){labels.push(i)}

new Chart(ctx, {
type: 'line',
data: {
    labels: labels,
    datasets: [
    {
        label: 'Blood Flow',
        data: bloodData,
        borderColor: 'red',
        fill: false,
        yAxisID: 'yBlood',
        pointRadius: 0
    },
    {
        label: 'Electric Flow',
        data: electricData,
        borderColor: 'blue',
        fill: false,
        yAxisID: 'yElectric',
        pointRadius: 0
    }
    ]
},
options: {
    responsive: false,
    maintainAspectRatio: false,

    scales: {
    x: {
        title: {
        display: true,
        text: 'Time (HH:MM:SS)'
        }
    },
    yBlood: {
        type: 'linear',
        position: 'left',
        text: 'Blood flow scale'
    },
    yElectric: {
        type: 'linear',
        position: 'right',
        text: 'Electric flow scale',
        min: 2000,
        max: 2500
    }
    }
}
});


}

