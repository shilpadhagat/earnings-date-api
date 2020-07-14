import React from 'react';
import './App.css';
import { Row, Col } from 'antd';
import { Table, Typography, Divider, Form, DatePicker, Input, Button, Alert, Layout } from 'antd';

const { Header, Content, Footer } = Layout;

const { Text } = Typography;

const apiUrl = 'https://us-east1-poised-lens-267620.cloudfunctions.net/get-earnings-call-date';

const columns = [
  {
    title: 'Date',
    dataIndex: 'date',
    key: 'date',
  },
  {
    title: 'Time',
    dataIndex: 'time',
    key: 'time',
  },
  {
    title: 'Ticker',
    dataIndex: 'ticker',
    key: 'ticker',
  },
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
  },
];

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      earnings_date: '',
      ticker: '',
      earnings_data: [],
      url: '',
      hasError: false,
      error: null,
    };
  }

  handleTickerChange = (event) => {
    this.setState({ticker: event.target.value})
  }

  handleDateChange = (date, dateString) => {
    this.setState({earnings_date: dateString})
  }

  fetchEarningsData = (event) => {
    let complete_url;
    if (this.state.earnings_date && this.state.ticker) {
      complete_url = `${apiUrl}?ticker=${this.state.ticker}&date=${this.state.earnings_date}`;
      this.setState({
        hasError: true,
        error: 'Provide either ticker or date not both',
        url: complete_url,
        earnings_data: null,
      });
      return;
    } else if (this.state.ticker) {
      complete_url = `${apiUrl}?ticker=${this.state.ticker}`;
    } else if (this.state.earnings_date) {
      complete_url = `${apiUrl}?date=${this.state.earnings_date}`;
    } else {
      complete_url = apiUrl;
      this.setState({
        url: complete_url,
        earnings_data: null,
      });
      return;
    }
    this.setState({url: complete_url});
    fetch(complete_url)
      .then((response) => {
        if (response.ok) {
          this.setState({hasError: false});
          return response.json();
        } else {
          throw new Error('Something went wrong ...');
        }
      })
      .then((data) => {
        this.setState({earnings_data: data})
      }).catch(error => {
        this.setState({error})
        console.log(error)});
    }

  render() {
    return (
      <Layout>
        <Header style={{ position: 'fixed', zIndex: 1, width: '100%', color: 'white', textAlign: 'center', fontFamily: 'Tahoma', fontSize: '25px' }}>
          <div className="App" />
          GET earnings_date
        </Header>
        <Content className="site-layout" style={{ padding: '0 50px', marginTop: 64 }}>
          <div className="site-layout-background" style={{ padding: 24, minHeight: 100 }}>
            <Text strong>URL:  {this.state.url}</Text>
            <Divider orientation="left" style={{ color: '#333', fontWeight: 'normal' }}>
            </Divider>
            <Form onFinish={this.fetchEarningsData}>
              <Row>
                <Col span={9} order={1} style={{ verticalAlign: 'middle'}}>
                  <Form.Item label="Date">
                    <DatePicker onChange={this.handleDateChange}/>
                  </Form.Item>
                </Col>
                <Col span={3} order={2} style={{ verticalAlign: 'middle', padding: '4px', color: 'blue'}}>
                  <Text style={{ color: '#096dd9'}}>or</Text>
                </Col>
                <Col span={9} order={3} style={{ verticalAlign: 'middle'}}>
                  <Form.Item label="Ticker">
                    <Input className="ticker-input" type="text" value={this.state.ticker}
                      onChange={this.handleTickerChange}/>
                    </Form.Item>
                </Col>
                <Col span={3} order={4} style={{ verticalAlign: 'middle'}}>
                  <Form.Item shouldUpdate>
                    <Button type="primary" htmlType="submit">GET</Button>
                  </Form.Item>
                </Col>
              </Row>
            </Form>
         </div>
         <div>
          {this.state.hasError &&
            <Alert message={this.state.error} type="error" />
           }
         </div>
         <Table dataSource={this.state.earnings_data} columns={columns} />
        </Content>
        <Footer style={{ textAlign: 'center' }}>Created by Shilpa Dhagat</Footer>
      </Layout>
    );
  }
}

export default App;
