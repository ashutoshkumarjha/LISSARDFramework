import { alpha, styled } from "@mui/material/styles";
import InputBase from "@mui/material/InputBase";
import SearchIcon from "@mui/icons-material/Search";
import * as React from "react";
import { useState } from "react";
import Popover from "@material-ui/core/Popover";
import Typography from "@material-ui/core/Typography";
import { useDispatch } from "react-redux";
import { addLayer, addSearchLayer, changeMapView } from "../actions";
import { generateId, loadparcelIdFromAddressId, fetchGetWithSignal } from "../utils/helpers";
import Config from '../config.js';


const Search = styled('div')(({ theme }) => ({
    position: 'relative',
    borderRadius: theme.shape.borderRadius,
    backgroundColor: alpha(theme.palette.common.white, 0.15),
    '&:hover': {
        backgroundColor: alpha(theme.palette.common.white, 0.25),
    },
    marginLeft: 0,
    width: '100%',
    [theme.breakpoints.up('sm')]: {
        marginLeft: theme.spacing(1),
        width: 'auto',
    },
}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
    padding: theme.spacing(0, 2),
    height: '100%',
    position: 'absolute',
    pointerEvents: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
    color: 'inherit',
    '& .MuiInputBase-input': {
        padding: theme.spacing(1, 1, 1, 0),
        // vertical padding + font size from searchIcon
        paddingLeft: `calc(1em + ${theme.spacing(4)})`,
        transition: theme.transitions.create('width'),
        width: '100%',
        [theme.breakpoints.up('sm')]: {
            width: '12ch',
            '&:focus': {
                width: '20ch',
            },
        },
    },
}));

const AddressSearch = () => {

    const dispatch = useDispatch();

    let [searchText, setSearchText] = useState('');
    let [searchResults, setSearchResults] = useState([]);
    let [ctrl, setCtrl] = useState(null);

    const [anchorEl, setAnchorEl] = useState(null);

    const queryAddress = (searchText, targetEle) => {
        setAnchorEl(null);
        setSearchResults([])
        if (!Boolean(searchText)) {
            return;
        }
        let addressUrl = `${Config.DATA_HOST}/data/searchAddress?searchText=${searchText}`;
        if (ctrl !== null) {
            ctrl.abort();
        }
        const controller = new AbortController();
        setCtrl(controller);
        let _pm = fetchGetWithSignal(addressUrl, controller.signal);
        _pm.then(result => {
            // console.log(result);
            let sr = [];
            for (let i = 0; i < result.data.length; i++) {
                sr.push({
                    gid: result.data[i]['gid'],
                    id: result.data[i]['address_id'],
                    name: result.data[i]['full_address'],
                    geom: JSON.parse(result.data[i]['geom']),
                })
            }
            // console.log("Promise", result);
            setSearchResults(sr);
            setAnchorEl(targetEle);
        })
            .catch(e => {

            })
    }

    return <div>
        <Search>
            <SearchIconWrapper>
                <SearchIcon />
            </SearchIconWrapper>
            <StyledInputBase
                placeholder="Search…"
                inputProps={{ 'aria-label': 'search' }}
                value={searchText}
                onChange={(e) => {
                    let text = e.target.value;
                    setSearchText(text);
                    // console.log(text, Boolean(text))
                    queryAddress(text, e.currentTarget);

                }}
            />
        </Search>



        <Popover
            open={Boolean(anchorEl)}
            anchorEl={anchorEl}
            onClose={() => {
                setAnchorEl(null);
            }}
            anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'left',
            }}
            disableAutoFocus={true}
            disableEnforceFocus={true}
        >
            {
                searchResults.map(r => {
                    return <Typography onClick={async () => {
                        setAnchorEl(null);
                        setSearchResults([]);
                        dispatch(changeMapView([r.geom.coordinates[1], r.geom.coordinates[0]], 18));
                        let parcel = await loadparcelIdFromAddressId(r.id);
                        console.log(parcel);
                        let searchLayerId = `address_search_${generateId(3)}`;
                        dispatch(addSearchLayer(searchLayerId));
                        dispatch(addLayer({
                            type: 'VECTOR_GJ',
                            id: searchLayerId,
                            active: true,
                            data: parcel.geometry,
                            name: 'Address Search',
                            sortOrder: -2,
                            showLegend: false,
                            showInLayerList: false
                        }))


                    }} key={r.id} sx={{ p: 2 }}>{r.name}</Typography>
                })
            }
        </Popover>


    </div>
}

export default AddressSearch;