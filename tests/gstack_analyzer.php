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

echo "gstack analyzer begin\n";

$thrd_num = 0;
$nnum = 0;

$handle = @fopen("gstack.log", "r");
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

echo count($global_stack);