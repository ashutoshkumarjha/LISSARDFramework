import { useEffect, useRef, useState } from "react";
import { Chart, registerables } from 'chart.js';
import { connect } from "react-redux";

Chart.register(...registerables);
const mapStateToProps = state => {
    return {
        map: state.MapReducer
    }
};

const MapChart = (props) => {
    const [chart, setChart] = useState(null)
    const canvasRef = useRef()
    const loadChart = (data) => {
            if(chart){
                chart.destroy()
            }
            try{
                setChart(
                    new Chart(canvasRef.current, {
                        type: data.type,
                        data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Pixel Values',
                            borderColor: 'rgb(75, 192, 192)',
                            data: data.values,
                            borderWidth: 1
                        }]
                        },
                        options: {
                            maintainAspectRatio: false
                        }
                    })
                )
            }catch(e){
                console.log(e)
            }
    }

    useEffect(()=>{
        if(props.map.chartData)
            loadChart(props.map.chartData)
    }, [props.map.chartData])

    return <div style={{
        position: 'absolute',
        bottom: 80,
        width: 'calc(100% - 500px)',
        zIndex: 500
        // left: 0

    }}>
        <canvas ref={canvasRef} id="chart-div"></canvas>
    </div>
}

export default connect(mapStateToProps)(MapChart);