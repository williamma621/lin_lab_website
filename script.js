let bflow = document.getElementById("b-flow")
let eflow = document.getElementById("e-flow")
let button1 = document.getElementById("generate-graph")
let textarea = document.querySelector('textarea');
button1.addEventListener('click', ()=> {
    const bflow_file = bflow.files[0];
    const eflow_file = eflow.files[0];
    const bflowReader = new FileReader();
    const eflowReader = new FileReader();
    bflowText = false
    eflowText = false;
    bflowReader.onload = () => {
        bflowText = bflowReader.result;
        blines = bflowText.split(/\r\n|\n/);
        plotGraph(); // check if both done
    };

    eflowReader.onload = () => {
        eflowText = eflowReader.result;
        elines = eflowText.split(/\r\n|\n/);
        plotGraph(); // check if both done
    };

    bflowReader.readAsText(bflow_file);
    eflowReader.readAsText(eflow_file);

});


function maybeDisplay() {
  if (bflowText && eflowText) {
    textarea.value = `Blood Flow:\n${bflowText}\n\nElectric Flow:\n${eflowText}`;
  }
}

function plotGraph(){
if (bflowText && eflowText){
const labels = [];
const bloodData = [];
const electricData = [];

for (let i = 45; i < 2049; i++){
const row = blines[i].split("\t");
const timestamp = `${row[1]}:${row[2]}:${row[3]}`;
labels.push(timestamp);
bloodData.push(parseFloat(row[4]));
}

for (let i = 21; i < 2035; i++){
    const row = elines[i].split(",");
    electricData.push(parseFloat(row[2]));
}

const ctx = document.getElementById('combined-chart').getContext('2d');

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
}
