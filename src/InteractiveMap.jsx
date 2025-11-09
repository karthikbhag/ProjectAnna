import Map from "./Map";
import Menu from "./Menu";
import StatCard from "./StatCard";
import React, { useState } from 'react';
import "./Interactive-Map.css"
import Graph from "./Graph";
import StatDash from "./StatDash";
import SelectionMenu from "./SelectionMenu";
import { DISASTERS } from "./data";
import SignificantEvent from "./SignificantEvent";
import Footer from "./Footer";

export default function InteractiveMap({locationData}) {
   
    const pins = locationData.filter((item) => item.location !== "");

    return(
        
       <div className="content-wrapper">
        <div className='Map-Menu-Container'>
            <div className='Map-Menu-Wrapper'>
            
                <Menu disasters = {filteredData}/>
                <div className="Map-Graph-Contain">
                    <Map Disasters ={pins}/>
                </div>
                
            </div>
            
        </div>
        <Footer></Footer>
        </div> 
    );
}
