#include <ros/ros.h>

#include <std_msgs/String.h>

#include <sensor_msgs/LaserScan.h>

#include <geometry_msgs/Twist.h>


ros::Publisher vel_pub;

static int nCount = 0;


void lidarCallback(const sensor_msgs::LaserScan::ConstPtr& scan)

{

int nNum = scan->ranges.size();


int nMid = nNum / 2;

float fMidDist = scan->ranges[0];

ROS_INFO("Point[%d] = %f", 0, fMidDist);
fMidDist = scan->ranges[270];
ROS_INFO("Point[%d] = %f", 270, fMidDist);


if (nCount > 0)

{

nCount--;

return;

}

/**
geometry_msgs::Twist vel_cmd;

if (fMidDist > 1.5f)

{

vel_cmd.linear.x = 0.05;

}

else

{

vel_cmd.angular.z = 0.3;

nCount = 50;

}

vel_pub.publish(vel_cmd);*/

}


int main(int argc, char** argv)

{

ros::init(argc, argv, "wpb_home_lidar_behavior");


ROS_INFO("wpb_home_lidar_behavior start!");


ros::NodeHandle nh;

ros::Subscriber lidar_sub = nh.subscribe("/scan", 10, &lidarCallback);

vel_pub = nh.advertise<geometry_msgs::Twist>("/cmd_vel", 10);


ros::spin();

}