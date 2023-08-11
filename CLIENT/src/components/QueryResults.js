import { connect, useDispatch } from "react-redux";
import AppModal from "./AppModal";
import { addLayer, toggleQueryResultsDialog } from "../actions";
import { Typography } from "@mui/material";
import { Button, TextField } from "@material-ui/core";
import { useState } from "react";

const mapStateToProps = (state) => {
    return {
        map: state.MapReducer,
        dialog: state.DialogReducer
    }
}

const QueryResults = (props) => {

    const dispatch = useDispatch();
    const [layerName, setLayerName] = useState("");

    if (props.map.queryResults.length <= 0) {
        return <></>;
    }
    let firstResult = props.map.queryResults[0];

    // const t = async () => {
    //     console.time("STA")
    //     for (let i = 0; i < 50; i++) {
    //         console.log("Fetch ", i)
    //         await fetch('https://test2.gishorizon.com/tilem/LISS3/8/183/105.png?tIndexes=870410314,871705583,871705563,880003475,879571713,859267663,858404194,857972449,880003455,870842077,859267683,870410334&bands=4,3,2&vmin=0&vmax=1&aoi_code=AVSQFSNWOYLMNOQG')
    //     }
    //     console.timeEnd("STA")
    // }
    // t();

    return <>
        <AppModal btnText={""} flag={props.dialog.showQueryResultsDialog} setFlag={(flag) => {
            dispatch(toggleQueryResultsDialog(flag))
        }}
            content=
            <div>
                <Typography variant="h6" gutterBottom component="div">
                    Add Layer
                </Typography>
                <br />
                <TextField
                    label="Layer name"
                    value={layerName}
                    onChange={(e) => {
                        setLayerName(e.target.value)
                    }} />
                <br />
                <ul style={{ maxHeight: 400, overflowY: 'auto', border: '1px solid grey' }}>
                    {
                        props.map.queryResults.map(r => {
                            return <li style={{ listStyle: 'none', margin: 4, padding: 8 }}>{r.dsName} <span style={{ float: 'right' }}>{new Date(r.ts).toLocaleString('in')}</span></li>
                        })
                    }
                </ul>
                <div style={{ textAlign: 'right' }}>
                    <Button color="primary" onClick={() => {
                        let lId = (Math.random() + 1).toString(36).substring(6);
                        let layer = {
                            type: 'DATA_TILE',
                            group: 'RASTER_DATA',
                            id: lId,
                            active: true,
                            tIndex: firstResult.tIndex,
                            tIndexes: props.map.queryResults.map(qr => qr.tIndex),
                            aoiCode: firstResult['aoiCode'],
                            dsId: firstResult['dsName'],
                            noOfBands: firstResult['dsData']['no_of_bands'],
                            name: layerName, // + ": " + firstResult.dsName,//'Layer: ' + firstResult.dsName + " #" + lId,
                            sortOrder: 0,
                            showLegend: false,
                            showInLayerList: true,
                            style: {
                                min: 0,
                                max: 1,
                                bands: [4, 3, 2],
                                type: "rgb"
                            }
                        }
                        dispatch(addLayer(layer));
                        dispatch(toggleQueryResultsDialog(false))
                    }}>Add</Button>
                </div>
            </div>
        />

    </>
}

export default connect(mapStateToProps)(QueryResults);