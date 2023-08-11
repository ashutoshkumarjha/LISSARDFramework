import * as React from 'react';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";

export default function IconMenuEl(props) {
    const [anchorEl, setAnchorEl] = React.useState(null);
    const open = Boolean(anchorEl);
    const handleClick = (event) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
        setAnchorEl(null);
    };

    return (
        <div>
            <Button
                variant={'contained'}
                aria-controls={open ? 'basic-menu' : undefined}
                aria-haspopup="true"
                aria-expanded={open ? 'true' : undefined}
                onClick={handleClick}
                style={{textTransform: 'none'}}
                startIcon={props.icon}
            >
                {props.name}
            </Button>
            <Menu
                color="inherit"
                anchorEl={anchorEl}
                open={open}
                onClose={handleClose}
                MenuListProps={{
                    'aria-labelledby': 'basic-button',
                }}
            >
                {
                    props.items.map(i=>{
                        return <MenuItem key={i.id} onClick={(e)=>{i.click(i.id);handleClose();}}>
                            <ListItemIcon>
                                {i.icon()}
                            </ListItemIcon>
                            <ListItemText>{i.name}</ListItemText>
                        </MenuItem>
                    })
                }
            </Menu>
        </div>
    );
}
