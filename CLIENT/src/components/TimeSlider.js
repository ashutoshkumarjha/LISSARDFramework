import { Slider } from "@mui/material";
import { useEffect, useState } from "react";
import { connect, useDispatch } from "react-redux";
import { addLayer, updateTimeIndex } from "../actions";

const mapStateToProps = state => {
    return {
        map: state.MapReducer
    }
};

const TimeSlider = (props) => {

    let timeValues = props.map.timeIndexes;
    const dispatch = useDispatch()

    const [tIndex, setTIndex] = useState(null)

    useEffect(()=>{
        if(!tIndex){
            return;
        }
        dispatch(updateTimeIndex(tIndex))
    }, [tIndex])

    useEffect(()=>{
        if(props.map.timeIndexes && props.map.timeIndexes.length>0)
            setTIndex(props.map.timeIndexes[0]['tIndex'])
    }, [props.map.timeIndexes])

    return <div style={{
        position: 'absolute',
        bottom: 20,
        width: 'calc(100% - 500px)',
        zIndex: 500
        // left: 0

    }}>
        {
            Boolean(timeValues)?(
                <Slider
                    aria-label="Data Time"
                    getAriaValueText={(ts)=>{
                        // return ""
                        return new Date(timeValues[ts]['ts']).toLocaleDateString('in')
                    }}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(v)=>{
                        return new Date(timeValues[v]['ts']).toLocaleDateString('in')
                    }}
                    step={1}
                    marks
                    min={0}
                    max={timeValues.length-1}
                    onChange={(e)=>{
                        let v = e.target.value
                        console.log(timeValues, v)
                        console.log(timeValues[v]['tIndex'])
                        // v = new Date(timeValues[v]['ts'])
                        setTIndex(timeValues[v]['tIndex'])
                    }}
                />
            ):''
        }
    </div>
}


export default connect(mapStateToProps)(TimeSlider);