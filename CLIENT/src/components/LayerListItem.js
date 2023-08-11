import React, { useState } from "react";
import { connect, useDispatch } from 'react-redux';
import Paper from '@mui/material/Paper';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import { changeLayerStyle, changeMapExtent, removeLayer, toggleLayerState } from '../actions/index';
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import DeleteIcon from '@mui/icons-material/Delete';
import IconButton from '@mui/material/IconButton';
import Grid from "@material-ui/core/Grid";
import DataService from "../services.js/Data";
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import PaletteIcon from '@mui/icons-material/Palette';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';
import { FormControl, InputLabel, MenuItem, Select, TextField } from "@material-ui/core";

const mapStateToProps = (state) => {
    return {
        map: state.MapReducer
    }
}

const LayerListItem = (props) => {
    const dispatch = useDispatch();
    const [showStyle, setShowStyle] = useState(false);
    const handleLayerToggle = (e) => {
        dispatch(toggleLayerState(props.layer.id, e.target.checked));
    }

    const changeVizBand = (color, band) => {
        let nLayer = { ...props.layer };
        nLayer.style.bands[color] = band;
        dispatch(changeLayerStyle(nLayer.id, nLayer.style))
    }

    const changeVizType = (styleType) => {
        let nLayer = { ...props.layer };
        nLayer.style.type = styleType;
        if (styleType === 'grey') {
            nLayer.style.bands = [nLayer.style.bands[0]];
        } else {
            nLayer.style.bands = [4, 3, 2];
        }
        dispatch(changeLayerStyle(nLayer.id, nLayer.style))
    }

    const changeMinValue = (value) => {
        let nLayer = { ...props.layer };
        // if (value === '') {
        //     value = 0;
        // }
        nLayer.style.min = value;
        dispatch(changeLayerStyle(nLayer.id, nLayer.style))
    }

    const changeMaxValue = (value) => {
        let nLayer = { ...props.layer };
        // if (value === '') {
        //     value = 0;
        // }
        nLayer.style.max = value;
        dispatch(changeLayerStyle(nLayer.id, nLayer.style))
    }

    return (
        <Paper elevation={2} style={{ padding: 8 }}>
            <Grid
                justifyContent="space-between" // Add it here :)
                container
                spacing={2}
            >
                <Grid item>
                    <FormControlLabel
                        control={<Checkbox
                            onChange={handleLayerToggle}
                            checked={props.layer.active} />}
                        label={<Typography variant={'caption'} >{props.layer.name}</Typography>}
                    />
                </Grid>
                <Grid item>
                    {/* {
                        props.layer.type!=='WMS' || !props.layer.showLegend ?'':(
                            <div style={{
                                paddingTop: 12
                            }}>
                                <img src={props.layer.url + '?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&WIDTH=20&HEIGHT=20&LAYER=' + props.layer.id}  alt={'legend'}/>
                            </div>
                        )
                    } */}
                    <IconButton onClick={() => {
                        //changeMapView
                        DataService.getAoiByCode(props.layer.aoiCode)
                            .then(r => {
                                let extent = JSON.parse(r.data.aoi_extent);
                                dispatch(changeMapExtent([
                                    [extent.coordinates[0][0][1], extent.coordinates[0][0][0]],
                                    [extent.coordinates[0][2][1], extent.coordinates[0][2][0]]
                                ]))
                            });
                    }} aria-label="zoom to">
                        <CenterFocusStrongIcon />
                    </IconButton>
                    {
                        props.layer.type === "DATA_TILE" || props.layer.type === "OUTPUT_DATA_TILE" || props.layer.type === "PREVIEW_DATA_TILE" ? (
                            <IconButton onClick={() => {
                                setShowStyle(!showStyle)
                            }}>
                                <PaletteIcon />
                            </IconButton>
                        ) : ''
                    }

                    <IconButton onClick={() => {
                        dispatch(removeLayer(props.layer.id))
                    }}>
                        <DeleteIcon />
                    </IconButton>
                </Grid>
            </Grid>

            {
                (props.layer.type === "DATA_TILE" || props.layer.type === "OUTPUT_DATA_TILE" || props.layer.type === "PREVIEW_DATA_TILE") && showStyle ? (
                    <>
                        <FormControl style={{ margin: 12, width: 250 }}>
                            <InputLabel>Style type</InputLabel>
                            <Select
                                value={props.layer.style.type}
                                label="Style"
                                onChange={(e) => { changeVizType(e.target.value) }}
                            >
                                <MenuItem key={'grey'} value={'grey'}>Grayscale</MenuItem>
                                <MenuItem key={'rgb'} value={'rgb'}>RGB</MenuItem>
                            </Select>
                        </FormControl>
                        <br />
                        {
                            props.layer.style.type === 'rgb' ? ['Red', 'Green', 'Blue'].map((c, i) => {
                                return <div style={{ margin: 8, padding: 8, backgroundColor: c === 'Red' ? '#FF4343' : c === 'Green' ? '#0EB22C' : '#2049B0', display: 'inline-block', borderRadius: 4 }}>
                                    <FormControl>
                                        <InputLabel style={{ color: 'white' }}>{c}</InputLabel>
                                        <Select value={props.layer.style.bands[i]} onChange={(e) => changeVizBand(i, e.target.value)}>
                                            {
                                                Array(props.layer.noOfBands).fill(0).map((v, i) => {
                                                    return <MenuItem style={{ color: c === 'Red' ? '#FF4343' : c === 'Green' ? '#0EB22C' : '#2049B0' }} key={i} value={i + 1}>{`B${i + 1}`}</MenuItem>
                                                })
                                            }
                                        </Select>
                                    </FormControl>
                                </div>
                            }) : <div style={{ margin: 8, padding: 8, backgroundColor: '#333', display: 'inline-block', borderRadius: 4 }}>
                                <FormControl>
                                    <InputLabel style={{ color: 'white' }}>Grey</InputLabel>
                                    <Select style={{ color: 'white' }} value={props.layer.style.bands[0]} onChange={(e) => changeVizBand(0, e.target.value)}>
                                        {
                                            Array(props.layer.noOfBands).fill(0).map((v, i) => {
                                                return <MenuItem style={{ color: '#333' }} key={i} value={i + 1}>{`B${i + 1}`}</MenuItem>
                                            })
                                        }
                                    </Select>
                                </FormControl>
                            </div>
                        }
                        <br />
                        <FormControl style={{ margin: 12, width: 100 }}>
                            <TextField type={"number"} value={props.layer.style.min} label="Min. value" variant="standard" onChange={(e) => { changeMinValue(e.target.value) }} />
                        </FormControl>
                        &nbsp;&nbsp;
                        <FormControl style={{ margin: 12, width: 100 }}>
                            <TextField type={"number"} value={props.layer.style.max} label="Max. value" variant="standard" onChange={(e) => { changeMaxValue(e.target.value) }} />
                        </FormControl>
                    </>
                ) : ''
            }


        </Paper>
    )
}

export default connect(mapStateToProps)(LayerListItem);
