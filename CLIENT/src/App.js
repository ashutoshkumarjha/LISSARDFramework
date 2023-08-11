import './App.css'
import * as React from 'react';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import CssBaseline from '@mui/material/CssBaseline';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';

import Map from './components/Map';
import LayersPanel from './components/LayersPanel';
import Grid from "@material-ui/core/Grid";
import AddressSearch from "./components/AddressSearch";
import TimeSlider from './components/TimeSlider';
import MapChart from './components/MapChart';
import ModelBuilder from './components/ModelBuilder';
import { Button } from '@material-ui/core';
import { connect, useDispatch } from 'react-redux';
import { toggleTasksDialog } from './actions';
import AppModal from './components/AppModal';
import TasksList from './components/TasksList';
import QueryPanel from './components/QueryPanel';
import AddAoiLayer from './components/AddAoiLayer';
import QueryResults from './components/QueryResults';

const drawerWidth = 0;


const mapStateToProps = (state) => {
    return {
        map: state.MapReducer,
        dialog: state.DialogReducer
    }
}

function App(props) {
    const [mobileOpen, setMobileOpen] = React.useState(false);
    const dispatch = useDispatch();

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    return (
        <Box sx={{ display: 'flex' }}>
            <CssBaseline />
            <AppBar
                position="fixed"
                sx={{
                    width: { sm: `calc(100% - ${drawerWidth}px)` },
                    ml: { sm: `${drawerWidth}px` },
                }}
            >
                <Toolbar>

                    <Grid
                        justifyContent="space-between" // Add it here :)
                        container
                        spacing={2}
                    >
                        <Grid item>
                            <Typography variant="h6" noWrap component="div">
                                Project
                            </Typography>
                        </Grid>
                    </Grid>


                    <AppModal btncolor={'white'} btnText={"Tasks"} flag={props.dialog.showTasksDialog} setFlag={(flag) => {
                        dispatch(toggleTasksDialog(flag))
                    }} content=<TasksList /> />


                </Toolbar>
            </AppBar>
            {/* <Box
                component="nav"
                sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
                aria-label="mailbox folders"
            >
                <Toolbar />
                <LayersPanel />
            </Box> */}
            <Box
                component="main"
                sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${drawerWidth}px)` } }}
            >
                <Toolbar />
                <Map />
                <LayersPanel />

                {/* <QueryPanel /> */}
                {/* <AddAoiLayer />


                <ModelBuilder />
                <QueryResults /> */}

                {/* <MapChart />
                <TimeSlider /> */}
            </Box>
        </Box>
    );
}

export default connect(mapStateToProps)(App);