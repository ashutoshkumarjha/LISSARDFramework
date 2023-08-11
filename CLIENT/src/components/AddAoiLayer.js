import * as React from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import DatePicker from 'react-datepicker';
import { Button, Slider, Tab, Tabs, Typography } from '@mui/material';
import { connect, useDispatch } from 'react-redux';
import { addLayer, setQueryResults, setTimeIndexes, toggleAddAoiDialog, toggleAddLayerDialog, toggleQueryResultsDialog, updateRGBBands } from '../actions';
import DataService from '../services.js/Data';
import Config from '../config.js';
import AppModal from './AppModal';

const mapStateToProps = (state) => {
    return {
        map: state.MapReducer,
        dialog: state.DialogReducer
    }
}

const AddAoiLayer = (props) => {

    const dispatch = useDispatch()

    const [datasets, setDatasets] = React.useState([])
    const [aoi, setAoi] = React.useState("")

    const [aoiGj, setAoiGj] = React.useState("")
    const [aoiName, setAoiName] = React.useState("")

    const getDatasets = () => {
        fetch(`${Config.DATA_HOST}/getAois`)
            .then(r => r.json())
            .then(r => {
                setDatasets(r.data.filter(v => v.aoi_name.indexOf('Temp') === -1).map(d => {
                    return {
                        name: d.aoi_name,
                        id: d.id,
                        code: d.aoi_code
                    }
                }))
            })
            .catch(er => console.log(er))
    }

    const getAoiByCode = (aoi) => {
        DataService.getAoiByCode(aoi)
            .then(r => {
                dispatch(addLayer({
                    type: 'VECTOR',
                    group: 'AOI',
                    id: `AOI_${aoi}`,
                    active: true,
                    data: JSON.parse(r.data.geom),
                    aoiCode: aoi,
                    name: r.data.aoi_name,
                    sortOrder: 0,
                    showLegend: false,
                    showInLayerList: true
                }))
                dispatch(toggleAddAoiDialog(false))
            }).catch(e => e);
    }

    const addAoi = () => {
        DataService.addAoi(JSON.stringify(JSON.parse(aoiGj)), aoiName)
            .then(r => {
                setAoi(r.data);
                getAoiByCode(r.data)
            }).catch(e => e);
    }

    React.useEffect(() => {
        getDatasets()
    }, [])

    const [selectedTab, setSelectedTab] = React.useState(0);

    const TabPanel = (props) => {
        const { value, index } = props;
        return (
            <div
                role="tabpanel"
                hidden={value !== index}
                id={`add-aoi-tabpanel-${index}`}
            >
                {value === index && (
                    <props.ChildComp />
                )}
            </div>
        )
    }

    return <AppModal btnText={"Add AOI"} height={350} flag={props.dialog.showAddAoiDialog} setFlag={(flag) => {
        dispatch(toggleAddAoiDialog(flag))
    }} content=<div>
        <Typography variant="h6" gutterBottom component="div">
            Add AOI
        </Typography>
        <Box sx={{ width: '100%' }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={selectedTab} onChange={(e, v) => {
                    setSelectedTab(v);
                }}>
                    <Tab label="Existing" />
                    <Tab label="Add new" />
                </Tabs>
            </Box>
            <div
                role="tabpanel"
                hidden={selectedTab !== 0}
            >
                <br />
                <FormControl fullWidth>
                    <InputLabel id="aoi-select">Existing AOI</InputLabel>
                    <Select
                        labelId="aoi-select"
                        value={aoi}
                        label="Existing AOI"
                        onChange={(e) => { setAoi(e.target.value) }}
                    >
                        {
                            datasets.map(ds => {
                                return <MenuItem key={ds.code} value={ds.code}>{`${ds.name} (${ds.code})`}</MenuItem>
                            })
                        }
                    </Select>
                </FormControl>
            </div>

            <div
                role="tabpanel"
                hidden={selectedTab !== 1}
            >
                <br />
                <FormControl fullWidth>
                    <TextField
                        label="AOI GeoJSON"
                        multiline
                        rows={4}
                        value={aoiGj}
                        onChange={(e) => {
                            setAoiGj(e.target.value)
                        }}
                    />
                </FormControl>

                <br />
                <br />
                <FormControl fullWidth>
                    <TextField
                        label="AOI Name"
                        value={aoiName}
                        onChange={(e) => {
                            setAoiName(e.target.value)
                        }}
                    />
                </FormControl>
            </div>
        </Box>
        <br />
        <br />
        <Button variant="contained" onClick={() => {
            if (selectedTab === 0) {
                getAoiByCode(aoi);
            } else {
                addAoi()
            }
        }}>Add</Button>
        <br />
    </div> />
}

export default connect(mapStateToProps)(AddAoiLayer);