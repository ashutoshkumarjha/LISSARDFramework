import {
    combineReducers
} from 'redux';
import MapReducer from "./MapReducer";
import DialogReducer from "./DialogReducer";

const rootReducer = combineReducers({
    MapReducer,
    DialogReducer
});

export default rootReducer;