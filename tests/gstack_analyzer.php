<?php

ini_set('memory_limit','256M');

$global_stack=array();
$i=0;

function parse_stack_item($buffer){
    global $i;
    if (strstr($buffer, "Thread")){
	$matches = null;
	$returnValue = preg_match('/Thread ([\\d]*) \\(Thread 0x[0-9A-Fa-f]{1,12} \\(LWP ([\\d]*)\\)\\):/', $buffer, $matches);
	if($returnValue){
	    if(count($matches)>2){
		$num = intval($matches[1]);
		$id = intval($matches[2]);
		if($num == 1) {
		    $i++;
		}
		return array($id, $num);
	    }
	}
    } else {
	$matches = null;
	$returnValue = preg_match('/#([\\d]*)[\\s]+0x[0-9A-Fa-f]{1,16} in ([\\w\\W]*(\\([\\S\\s]*\\))*) \\(\\)/', $buffer, $matches);
	if($returnValue){
	    if(count($matches)>2){
		$num = intval($matches[1]);
		return array('a', $num, $matches[2]);
	    }
	}
    }
    return array();
}

function list_all_used_functions(&$arr){
    $len = count($arr);
    $names=array();
    for($i=0;$i<$len;$i++){
	foreach($arr[$i] as $key=>$value){
	    foreach($value as $key1=>$value1){
		if(!in_array($value1, $names)) $names[]=$value1;
	    }
	}
    }
    sort($names);
    $len = count($names);
    for($i=0;$i<$len;$i++){
	echo $names[$i]."\n";
    }
}

function list_count_of_function(&$arr, $func_name){
    $len = count($arr);
    $names=array();
    $total = 0;
    for($i=0;$i<$len;$i++){
	$count = 0;
	foreach($arr[$i] as $key=>$value){
	    foreach($value as $key1=>$value1){
		if($value1==$func_name) $count++;
	    }
	}
	echo "Snapshot ".$i." found functions: ".$count."\n";
	$total+=$count;
    }
    echo "Total amounts: ".$total."\n";
}

function list_parent_for_function_level(&$arr, $func_name,$level){
    $len = count($arr);
    $names=array();
    $counts=array();
    for($i=0;$i<$len;$i++){
	foreach($arr[$i] as $key=>$value){
	    foreach($value as $key1=>$value1){
		if($value1==$func_name){
		   $keys = array_keys($value);
		   $jj=0;
		   while($keys[$jj]!=$key1) $jj++;
		   $stp = $jj + $level;
		   if($stp>=count($keys)) $stp = count($keys) - 1;
		   if(!in_array($value[$keys[$stp]], $names)) {
		    $names[]=$value[$keys[$stp]];
		    $counts[$value[$keys[$stp]]]=1;
		   } else {
		    $counts[$value[$keys[$stp]]]++;
		   }
		}
	    }
	}
    }
    asort($counts);
    foreach($counts as $key=>$value){
	echo $key." with counts ".$value."\n";
    }
}

function list_stack_down_for_function(&$arr, $func_name,$level){
    $len = count($arr);
    for($i=0;$i<$len;$i++){
	foreach($arr[$i] as $key=>$value){
	    foreach($value as $key1=>$value1){
		if($value1==$func_name){
		   $keys = array_keys($value);
		   $jj=0;
		   while($keys[$jj]!=$key1) $jj++;
		   $stp = $jj - $level;
		   if($stp<0) $stp = 0;
		   echo "Found function in ".$i." iteration, thread ".$key."\n";
		   for($kk=$jj;$kk>=$stp;$kk--){
		    echo "frame #".$keys[$kk]. " function ".$value[$keys[$kk]]."\n";
		   }
		   break;
		}
	    }
	}
    }
}

$longopts  = array(
    "list",     
    "countfunc:",    
    "parentfunc:",        
    "stackdown:",           
    "level:"
);

$options = getopt("f:", $longopts);
if(isset($options["f"])){
    $fname = $options["f"];
} else {
    $fname = "gstack.log";
}

$tt=0;
if (isset($options["list"])){
$tt=1;
}

if (isset($options["countfunc"])){
$tt=2;
$func_name = $options["countfunc"];
}

if (isset($options["parentfunc"])){
$tt=3;
$func_name = $options["parentfunc"];
}

if (isset($options["stackdown"])){
$tt=4;
$func_name = $options["stackdown"];
}

$level=2;
if (isset($options["level"])){
$level = intval($options["level"]);
if($level<0) $level=0;
}

echo "gstack analyzer begin\n";

$thrd_num = 0;
$nnum = 0;

$handle = @fopen($fname, "r");
if ($handle) {
    while (($buffer = fgets($handle, 4096)) !== false) {
        $res = parse_stack_item($buffer);
        if(count($res)==2){
    	    $thrd_num = $res[0];
    	    $nnum = $res[1];
        }
        if(count($res)==3){
    	    if($res[2]=="??") continue;
    	    if($nnum==1){
    		$global_stack[$i-1][$thrd_num][$res[1]]=$res[2];
    	    } else {
    		$global_stack[$i][$thrd_num][$res[1]]=$res[2];
    	    }
        }
    }
    if (!feof($handle)) {
        echo "Error: unexpected fgets() fail\n";
    }
    fclose($handle);
}

if($thrd_num>0){
	    if($nnum==1){
    		$global_stack[$i-1][$thrd_num][$res[1]]=$res[2];
    	    } else {
    		$global_stack[$i][$thrd_num][$res[1]]=$res[2];
    	    }
}

switch($tt){
case 1:
list_all_used_functions($global_stack);
break;
case 2:
list_count_of_function($global_stack, $func_name);
break;
case 3:
list_parent_for_function_level($global_stack, $func_name, $level);
break;
case 4:
list_stack_down_for_function($global_stack, $func_name, $level);
break;
default:
    echo "Usage: utility -f filename for analyzis [OPTIONS]\n";
    echo "OPTIONS:\n";
    echo "list - list all finded functions in stacktrace\n";     
    echo "countfunc=func_name - find counts of function in stacktrace\n";    
    echo "parentfunc=func_name --level - find parent of function, parent up with level\n";        
    echo "stackdown=func_name --level - print stacktrace down with level from func\n";           
    echo "level - level value for previous parameters\n";
}