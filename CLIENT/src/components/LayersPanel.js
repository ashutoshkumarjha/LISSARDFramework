import React, { useEffect, useState } from "react";
import LayerList from '../components/LayerList';
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import QueryPanel from "./QueryPanel";
import AppModal from "./AppModal";
import { connect, useDispatch } from "react-redux";
import { toggleAddAoiDialog, toggleAddLayerDialog, toggleTasksDialog } from "../actions";
import ModelBuilder from "./ModelBuilder";
import QueryResults from "./QueryResults";
import TasksList from './TasksList';
import go from 'gojs'

import DataTable from 'react-data-table-component';
import AddAoiLayer from "./AddAoiLayer";

const mapStateToProps = (state) => {
    return {
        map: state.MapReducer,
        dialog: state.DialogReducer
    }
}

const LayersPanel = (props) => {

    const dispatch = useDispatch();

    return <Paper elevation={2} style={{ padding: 15, maxHeight: 'calc(100vh - 120px)', overflowY: 'auto', zIndex: 1000, position: 'absolute', top: 100, right: 40 }}>
        {/* <Typography variant="h6" gutterBottom component="div">
            Layers
        </Typography> */}
        <LayerList />
        <QueryPanel />
        <AddAoiLayer />


        <ModelBuilder />
        <QueryResults />
    </Paper>
}

export default connect(mapStateToProps)(LayersPanel);