#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/tap-bridge-module.h"

using namespace ns3;

int main(int argc, char *argv[]) {
    Time::SetResolution(Time::NS);

    CommandLine cmd;
    cmd.Parse(argc, argv);

    // **Node0 = Broker (TAP Bridge ke Host)**
    // **Node1 = Subscriber (NS3 internal)**
    NodeContainer nodes;
    nodes.Create(2);

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue("10Mbps"));
    p2p.SetChannelAttribute("Delay", StringValue("50ms"));
    NetDeviceContainer devices = p2p.Install(nodes);

    InternetStackHelper stack;
    stack.Install(nodes);

    Ipv4AddressHelper address;
    address.SetBase("10.0.0.0", "255.255.255.0");
    Ipv4InterfaceContainer iface = address.Assign(devices);

    // ============================ TAP BRIDGE BROKER ============================
    TapBridgeHelper tap;
    tap.SetAttribute("Mode", StringValue("UseLocal"));
    tap.SetAttribute("DeviceName", StringValue("tap-mqtt"));
    tap.Install(nodes.Get(0), devices.Get(0));
    // Broker akan dapat IP ns3: 10.0.0.1

    // =============================== SUBSCRIBER ===============================
    // Diwakili sebagai UDP Echo Server pada port MQTT 1883
    UdpEchoServerHelper mqttBroker(1883);
    ApplicationContainer server = mqttBroker.Install(nodes.Get(1));
    server.Start(Seconds(1.0));
    server.Stop(Seconds(600.0));

    // =============================== PUBLISHER ===============================
    // Ini mewakili MQTT publish dari node broker ke subscriber
    UdpEchoClientHelper publisher(iface.GetAddress(1), 1883);
    publisher.SetAttribute("MaxPackets", UintegerValue(1000));
    publisher.SetAttribute("Interval", TimeValue(MilliSeconds(100))); // 10 msg/det
    publisher.SetAttribute("PacketSize", UintegerValue(64));

    ApplicationContainer client = publisher.Install(nodes.Get(0));
    client.Start(Seconds(5.0));   // publish setelah TAP aktif
    client.Stop(Seconds(600.0));

    Simulator::Stop(Seconds(600.0));
    Simulator::Run();
    Simulator::Destroy();

    return 0;
}
