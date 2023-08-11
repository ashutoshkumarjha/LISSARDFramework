import React, { useRef, useState, useEffect, useCallback } from "react";
import ModelComponent from "./ModelComponent";
//3C9655
/// throttle.ts
export const throttle = (f) => {
    let token = null,
        lastArgs = null;
    const invoke = () => {
        f(...lastArgs);
        token = null;
    };
    const result = (...args) => {
        lastArgs = args;
        if (!token) {
            token = requestAnimationFrame(invoke);
        }
    };
    result.cancel = () => token && cancelAnimationFrame(token);
    return result;
};

/// use-draggable.ts
const id = (x) => x;
// complex logic should be a hook, not a component
const useDraggable = ({ onDrag = id } = {}) => {
    // this state doesn't change often, so it's fine
    const [pressed, setPressed] = useState(false);

    // do not store position in useState! even if you useEffect on
    // it and update `transform` CSS property, React still rerenders
    // on every state change, and it LAGS
    const position = useRef({ x: 0, y: 0 });
    const ref = useRef();

    // we've moved the code into the hook, and it would be weird to
    // return `ref` and `handleMouseDown` to be set on the same element
    // why not just do the job on our own here and use a function-ref
    // to subscribe to `mousedown` too? it would go like this:
    const unsubscribe = useRef();
    const legacyRef = useCallback((elem) => {
        // in a production version of this code I'd use a
        // `useComposeRef` hook to compose function-ref and object-ref
        // into one ref, and then would return it. combining
        // hooks in this way by hand is error-prone

        // then I'd also split out the rest of this function into a
        // separate hook to be called like this:
        // const legacyRef = useDomEvent('mousedown');
        // const combinedRef = useCombinedRef(ref, legacyRef);
        // return [combinedRef, pressed];
        ref.current = elem;
        if (unsubscribe.current) {
            unsubscribe.current();
        }
        if (!elem) {
            return;
        }
        const handleMouseDown = (e) => {
            // don't forget to disable text selection during drag and drop
            // operations
            e.target.style.userSelect = "none";
            setPressed(true);
        };
        elem.addEventListener("mousedown", handleMouseDown);
        unsubscribe.current = () => {
            elem.removeEventListener("mousedown", handleMouseDown);
        };
    }, []);
    // useEffect(() => {
    //   return () => {
    //     // this shouldn't really happen if React properly calls
    //     // function-refs, but I'm not proficient enough to know
    //     // for sure, and you might get a memory leak out of it
    //     if (unsubscribe.current) {
    //       unsubscribe.current();
    //     }
    //   };
    // }, []);

    useEffect(() => {
        // why subscribe in a `useEffect`? because we want to subscribe
        // to mousemove only when pressed, otherwise it will lag even
        // when you're not dragging
        if (!pressed) {
            return;
        }

        // updating the page without any throttling is a bad idea
        // requestAnimationFrame-based throttle would probably be fine,
        // but be aware that naive implementation might make element
        // lag 1 frame behind cursor, and it will appear to be lagging
        // even at 60 FPS
        const handleMouseMove = //throttle(
            (event) => {
                // needed for TypeScript anyway
                if (!ref.current || !position.current) {
                    return;
                }
                const pos = position.current;
                // it's important to save it into variable here,
                // otherwise we might capture reference to an element
                // that was long gone. not really sure what's correct
                // behavior for a case when you've been scrolling, and
                // the target element was replaced. probably some formulae
                // needed to handle that case. TODO
                const elem = ref.current;
                position.current = onDrag({
                    x: pos.x + event.movementX,
                    y: pos.y + event.movementY
                });
                elem.style.transform = `translate(${pos.x}px, ${pos.y}px)`;
            }
        //);
        function collision($div1, $div2) {
            var x1 = $div1.getBoundingClientRect().left;
            var y1 = $div1.getBoundingClientRect().top;
            var h1 = $div1.getBoundingClientRect().height;
            var w1 = $div1.getBoundingClientRect().width;
            var b1 = y1 + h1;
            var r1 = x1 + w1;
            var x2 = $div2.getBoundingClientRect().left;
            var y2 = $div2.getBoundingClientRect().top;
            var h2 = $div2.getBoundingClientRect().height
            var w2 = $div2.getBoundingClientRect().width
            var b2 = y2 + h2;
            var r2 = x2 + w2;
            if (b1 < y2 || y1 > b2 || r1 < x2 || x1 > r2) return false;
            return true;
        }
        const handleMouseUp = (e) => {
            e.target.style.userSelect = "auto";
            setPressed(false);
            //check if any component is intersecting
            let c = document.querySelectorAll('.model-component')
            c.forEach(element=>{
                if(e.target === element){
                    return;
                }
                let collisionFlag = collision(e.target, element)
                if(collisionFlag){
                    element.style.background = 'red';
                    let transformValues = e.target.style.transform.replace("translate(", "").replace(")", "").replace("px", "").replace("px", "").split(",").map(v=>parseFloat(v.trim()))
                    let originValues = [
                        e.target.getBoundingClientRect().x - transformValues[0],
                        e.target.getBoundingClientRect().y - transformValues[1]
                    ];
                    let elemPos = [element.getBoundingClientRect().x, element.getBoundingClientRect().y]
                    console.log(originValues, elemPos, e.target.style.transform);
                    console.log(originValues[0]-elemPos[0], originValues[1]-elemPos[1])
                    // let newLoc = [originValues[0] - e.target.getBoundingClientRect().x, originValues[1] - e.target.getBoundingClientRect().y]
                    // setTimeout(()=>{
                    //     console.log(`translate(${-(originValues[0]-elemPos[0])}px, ${-(originValues[1]-elemPos[1])}px)`)
                        e.target.style.transform = `translate(${-(originValues[0]-elemPos[0])}px, ${-(originValues[1]-elemPos[1]) + 100}px)`;
                    // }, 500)
                    // element.style.translate = ''
                }else{
                    element.style.background = 'green'
                }
            })
        };
        // subscribe to mousemove and mouseup on document, otherwise you
        // can escape bounds of element while dragging and get stuck
        // dragging it forever
        document.addEventListener("mousemove", handleMouseMove);
        document.addEventListener("mouseup", handleMouseUp);
        return () => {
            // handleMouseMove.cancel();
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
        // if `onDrag` wasn't defined with `useCallback`, we'd have to
        // resubscribe to 2 DOM events here, not to say it would mess
        // with `throttle` and reset its internal timer
    }, [pressed, onDrag]);

    // actually it makes sense to return an array only when
    // you expect that on the caller side all of the fields
    // will be usually renamed
    return [legacyRef, pressed];

    // > seems the best of them all to me
    // this code doesn't look pretty anymore, huh?
};



const DraggableComponent = (props) => {
    /// example.ts
    const quickAndDirtyStyle = props.type === 'input' ? (
        {
            width: "200px",
            height: "100px",
            background: "#1B9625",
            color: "#FFFFFF",
            display: "inline-flex",
            justifyContent: "center",
            alignItems: "center"
        }
    ) : props.type === 'operation' ? (
        {
            width: "200px",
            height: "100px",
            background: "#CD853C",
            color: "#FFFFFF",
            display: "inline-flex",
            justifyContent: "center",
            alignItems: "center"
        }
    ) : {
        width: "200px",
        height: "100px",
        background: "#2B5EC3",
        color: "#FFFFFF",
        display: "inline-flex",
        justifyContent: "center",
        alignItems: "center"
    }
    // handlers must be wrapped into `useCallback`. even though
    // resubscribing to `mousedown` on every tick is quite cheap
    // due to React's event system, `handleMouseDown` might be used
    // in `deps` argument of another hook, where it would really matter.
    // as you never know where return values of your hook might end up,
    // it's just generally a good idea to ALWAYS use `useCallback`

    // it's nice to have a way to at least prevent element from
    // getting dragged out of the page
    const handleDrag = useCallback(
        ({ x, y }) => ({
            x: x,//Math.max(0, x),
            y: y//Math.max(0, y)
        }),
        []
    );

    const [ref, pressed] = useDraggable({
        onDrag: handleDrag
    });

    return (
        <div className="model-component" ref={ref} style={quickAndDirtyStyle}>
            {/* <p>{pressed ? "Input" : "Input"}</p> */}
            {/* <p>{props.name}</p> */}
            <ModelComponent {...props} />
        </div>
    );
};

export default DraggableComponent;