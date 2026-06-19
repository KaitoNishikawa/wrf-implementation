# Numerical Gaussian Processes for Time-dependent and Non-linear Partial Differential Equations

Maziar Raissi<sup>1</sup>, Paris Perdikaris<sup>2</sup>, and George Em Karniadakis<sup>1</sup>

<sup>1</sup>Division of Applied Mathematics, Brown University, Providence, RI, 02912, USA <sup>2</sup>Department of Mechanical Engineering, Massachusetts Institute of Technology, Cambridge, MA, 02139, USA

#### Abstract

We introduce the concept of numerical Gaussian processes, which we define as Gaussian processes with covariance functions resulting from temporal discretization of time-dependent partial differential equations. Numerical Gaussian processes, by construction, are designed to deal with cases where: (1) all we observe are noisy data on black-box initial conditions, and (2) we are interested in quantifying the uncertainty associated with such noisy data in our solutions to time-dependent partial differential equations. Our method circumvents the need for spatial discretization of the differential operators by proper placement of Gaussian process priors. This is an attempt to construct structured and data-efficient learning machines, which are explicitly informed by the underlying physics that possibly generated the observed data. The effectiveness of the proposed approach is demonstrated through several benchmark problems involving linear and nonlinear time-dependent operators. In all examples, we are able to recover accurate approximations of the latent solutions, and consistently propagate uncertainty, even in cases involving very long time integration.

Keywords: probabilistic machine learning, linear multi-step methods, Runge-Kutta methods, Bayesian modeling, uncertainty quantification

#### 1. Introduction

Data-driven methods are taking center stage across many disciplines of science, and machine learning techniques have achieved groundbreaking results across a diverse spectrum of pattern recognition tasks [1, 2, 3, 4, 5]. Despite their disruptive implications, many of these methods are blind to any underlying laws of physics that may have shaped the distribution of the observed data. A natural question would then be how one can construct efficient learning machines that explicitly leverage such structured prior information? To answer this question we have to turn our attention to the immense collective knowledge originating from centuries of research in applied mathematics and mathematical physics. Modeling the physical world through the lens of mathematics typically translates into deriving conservation laws from first principles, which often take the form of systems of partial differential equations. In many practical settings, the solution of such systems is only accessible by means of numerical algorithms that provide sensible approximations to given quantities of interest. In this work, we aim to capitalize on the long-standing developments of classical methods in numerical analysis and revisit partial differential equations from a statistical inference viewpoint. The merits of this approach are twofold. First, it enables the construction of data-efficient learning machines that can encode physical conservation laws as structured prior information. Second, it allows the design of novel numerical algorithms that can seamlessly blend equations and noisy data, infer latent quantities of interest (e.g., the solution to a partial differential equation), and naturally quantify uncertainty in computations. This approach is aligned in spirit with the emerging field of probabilistic numerics [6], which roots all the way back to Poincaré's courses on probability theory [7], and has been recently revived by the pioneering works of [8, 9, 10, 11].

To illustrate the key ingredients of this study, let us start by considering linear<sup>1</sup> partial differential equations of the form

$$u_t = \mathcal{L}_x u, \ x \in \Omega, \ t \in [0, T], \tag{1}$$

where  $\mathcal{L}_x$  is a linear operator and u(t,x) denotes the latent solution. As an example, the one dimensional heat equation corresponds to the case where

<sup>&</sup>lt;sup>1</sup>Non-linear equations have to be studied on a case by case basis (see e.g., section 2.6).

 $\mathcal{L}_x = \frac{\partial^2}{\partial x^2}$ . Moreover,  $\Omega$  is a subset of  $\mathbb{R}^D$ . All we observe are noisy data  $\{x^0, u^0\}$  on the black-box initial function u(0, x) as well as some information on the domain boundary  $\partial\Omega$  to be specified later. Our goal is to predict the latent solution u(t, x) at t > 0, and propagate the uncertainty due to noise in the initial data. For starters, let us try to convey the main ideas of this work using the Euler time stepping scheme

$$u^n = u^{n-1} + \Delta t \mathcal{L}_x u^{n-1}. \tag{2}$$

Here,  $u^n(x) = u(t^n, x)$ . Building upon Raissi et al. [12, 13], we place a Gaussian process [14] prior on  $u^{n-1}$ , i.e.,

$$u^{n-1}(x) \sim \mathcal{GP}(0, k_{u,u}^{n-1,n-1}(x, x', \theta)).$$
 (3)

Here,  $\theta$  denotes the hyper-parameters of the covariance function  $k_{u,u}^{n-1,n-1}$ . Gaussian process regression (see [14, 15]) is a non-parametric Bayesian machine learning technique that provides a flexible prior distribution over functions, enjoys analytical tractability, and has a fully probabilistic work-flow that returns robust posterior variance estimates, which quantify uncertainty in a natural way. Moreover, Gaussian processes are among a class of methods known as kernel machines (see [16, 17, 18]) and are analogous to regularization approaches (see [19, 20, 21]). They can also be viewed as a prior on one-layer feed-forward Bayesian neural networks with an infinite number of hidden units [22]. The Gaussian process prior assumption (3) along with the Euler scheme (2) will allow us to capture the entire structure of the differential operator  $\mathcal{L}_x$  as well as the Euler time-stepping rule in the resulting multi-output Gaussian process

$$\begin{bmatrix} u^n \\ u^{n-1} \end{bmatrix} \sim \mathcal{GP} \left( 0, \begin{bmatrix} k_{u,u}^{n,n} & k_{u,u}^{n,n-1} \\ k_{u,u}^{n-1,n-1} \end{bmatrix} \right). \tag{4}$$

The specific forms of the kernels  $k_{u,u}^{n,n}$  and  $k_{u,u}^{n,n-1}$  are direct functions of the Euler scheme (2) as well as the prior assumption (3), and will be discussed in more detail later. The multi-output process (4) is an example of a numerical Gaussian process, because the covariance functions  $k_{u,u}^{n,n}$  and  $k_{u,u}^{n,n-1}$  result from a numerical scheme, in this case, the Euler method. Essentially, this introduces a structured prior that explicitly encodes the physical law modeled by the partial differential equation (1). In the following, we will generalize the framework outlined above to arbitrary linear multi-step methods, originally

Table 1: Some specific members of the family of linear multi-step methods (5).

| Forward Euler    | $u^n = u^{n-1} + \Delta t \mathcal{L}_x u^{n-1}$                                                            |
|------------------|-------------------------------------------------------------------------------------------------------------|
| Backward Euler   | $u^n = u^{n-1} + \Delta t \mathcal{L}_x u^n$                                                                |
| Trapezoidal Rule | $u^{n} = u^{n-1} + \frac{1}{2}\Delta t \mathcal{L}_{x} u^{n-1} + \frac{1}{2}\Delta t \mathcal{L}_{x} u^{n}$ |

proposed by Bashforth and Adams [23], as well as Runge-Kutta methods, generally attributed to Runge [24]. The biggest challenge here is the proper placement of the Gaussian process prior (see e.g., equation (3)) in order to avoid inversion of differential operators and to bypass the classical need for spatial discretization of such operators. For instance, in the above example (see equations (2) and (3)), it would have been an inappropriate choice to start by placing a Gaussian process prior on  $u^n$ , rather than on  $u^{n-1}$ , as obtaining the numerical Gaussian process (4) would then involve inverting operators of the form  $I+\Delta t\mathcal{L}_x$  corresponding to the Euler method. Moreover, propagating the uncertainty associated with the noisy initial observations  $\{x^0, u^0\}$  through time is another major challenge addressed in the following.

#### 2. Linear Multi-step Methods

Let us start with the most general form of the linear multi-step methods [25] applied to equation (1); i.e.,

$$u^{n} = \sum_{i=1}^{m} \alpha_{i} u^{n-i} + \Delta t \sum_{i=0}^{m} \beta_{i} \mathcal{L}_{x} u^{n-i}.$$
 (5)

Different choices for the parameters  $\alpha_i$  and  $\beta_i$  result in specific schemes. For instance, in table 1, we present some specific members of the family of linear multi-step methods (5). We encourage the reader to keep these special cases in mind while reading the rest of this section. Linear multi-step methods (5) can be equivalently written as

$$\mathcal{P}_x u^n = \sum_{i=1}^m \mathcal{Q}_x^i u^{n-i},\tag{6}$$

Table 2: Some special cases of equation (6).

| Forward Euler    | $u^n = \mathcal{Q}_x u^{n-1}$                                        |
|------------------|----------------------------------------------------------------------|
|                  | $Q_x u^{n-1} = u^{n-1} + \Delta t \mathcal{L}_x u^{n-1}$             |
| Backward Euler   | $\mathcal{P}_x u^n = u^{n-1}$                                        |
|                  | $\mathcal{P}_x u^n = u^n - \Delta t \mathcal{L}_x u^n$               |
| Trapezoidal Rule | $\mathcal{P}_x u^n = \mathcal{Q}_x u^{n-1}$                          |
|                  | $\mathcal{P}_x u^n = u^n - \frac{1}{2} \Delta t \mathcal{L}_x u^n$   |
|                  | $Q_x u^{n-1} = u^{n-1} + \frac{1}{2} \Delta t \mathcal{L}_x u^{n-1}$ |

Table 3: Some special cases of equation (7).

| Forward Euler    | $u^n = \mathcal{Q}_x u^{n-1}$                           |
|------------------|---------------------------------------------------------|
|                  | $\tau = 0$                                              |
| Backward Euler   | $\mathcal{P}_x u^n = u^{n-1}$                           |
|                  | $\tau = 1$                                              |
| Trapezoidal Rule | $\mathcal{P}_x u^n = u^{n-1/2} = \mathcal{Q}_x u^{n-1}$ |
|                  | $\tau = 1/2$                                            |

where  $\mathcal{P}_x u := u - \Delta t \beta_0 \mathcal{L}_x u$  and  $\mathcal{Q}_x^i u := \alpha_i u + \Delta t \beta_i \mathcal{L}_x u$ . Some special cases of equation (6) are given in table 2. For every  $j = 0, 1, \ldots, m$  and some  $\tau \in [0, 1]$  which depends on the specific choices for the values of the parameters  $\alpha_i$  and  $\beta_i$ , we define  $u^{n-j+\tau}$  to be given by

$$\mathcal{P}_x u^{n-j+1} =: u^{n-j+\tau} := \sum_{i=1}^m \mathcal{Q}_x^i u^{n-i-j+1}. \tag{7}$$

Definition (7) takes the specific forms given in table 3 for some example schemes. Shifting every term involved in the above definition (7) by  $-\tau$ 

yields

$$\mathcal{P}_x u^{n-j+1-\tau} = u^{n-j} = \sum_{i=1}^m \mathcal{Q}_x^i u^{n-i-j+1-\tau}.$$
 (8)

To give an example, for the trapezoidal rule we obtain  $\mathcal{P}_x u^{n+1/2} = u^n = \mathcal{Q}_x u^{n-1/2}$  and  $\mathcal{P}_x u^{n-1/2} = u^{n-1} = \mathcal{Q}_x u^{n-3/2}$ . Therefore, as a direct consequence of equation (8) we have

$$u^{n} = \sum_{i=1}^{m} \mathcal{Q}_{x}^{i} u^{n-i+1-\tau}, \quad \text{when} \quad j = 0,$$

$$u^{n-j} = \mathcal{P}_{x} u^{n-j+1-\tau}, \quad \text{when} \quad j = 1, \dots, m.$$

$$(9)$$

This, in the special case of the trapezoidal rule, translates to  $u^n = \mathcal{Q}_x u^{n-1/2}$  and  $u^{n-1} = \mathcal{P}_x u^{n-1/2}$ . It is worth noting that by assuming  $u^{n-1/2}(x) \sim \mathcal{GP}(0, k(x, x'; \theta))$ , we can capture the entire structure of the trapezoidal rule in the resulting joint distribution of  $u^n$  and  $u^{n-1}$ . This proper placement of the Gaussian process prior is key to the proposed methodology as it allows us to avoid any spatial discretization of differential operators since no inversion of such operators is necessary. We will capitalize on this idea in the following.

## 2.1. Prior

Assuming that

$$u^{n-j+1-\tau}(x) \sim \mathcal{GP}(0, k^{j,j}(x, x'; \theta_j)), \quad j = 1, \dots, m,$$
 (10)

are m independent processes, we obtain the following  $numerical\ Gaussian\ process$ 

$$\begin{bmatrix} u^n \\ \vdots \\ u^{n-m} \end{bmatrix} \sim \mathcal{GP} \left( 0, \begin{bmatrix} k_{u,u}^{n,n} & \cdots & k_{u,u}^{n,n-m} \\ & \ddots & \vdots \\ & & k_{u,u}^{n-m,n-m} \end{bmatrix} \right),$$

where

$$k_{u,u}^{n,n} = \sum_{i=1}^{m} \mathcal{Q}_{x}^{i} \mathcal{Q}_{x'}^{i} k^{i,i}, \quad k_{u,u}^{n,n-j} = \mathcal{Q}_{x}^{j} \mathcal{P}_{x'} k^{j,j}, k_{u,u}^{n-i,n-j} = 0, \quad i \neq j, \quad k_{u,u}^{n-j,n-j} = \mathcal{P}_{x} \mathcal{P}_{x'} k^{j,j}, \quad j = 1, \dots, m.$$

$$(11)$$

It is worth noting that the entire structure of linear multi-step methods (5) is captured by the kernels given in equations (11). Note that although

we start from an independence assumption in equation (10), the resulting numerical Gaussian process exhibits a fully correlated structure as illustrated in equations (11). Moreover, the information on the boundary  $\partial\Omega$  of the domain  $\Omega$  can often be summarized by noisy observations  $\{\boldsymbol{x}_b^n, \boldsymbol{u}_b^n\}$  of a linear transformation  $\mathcal{B}_x$  of  $u^n$ ; i.e., noisy data on

$$u_b^n := \mathcal{B}_x u^n$$
.

Using this, we obtain the following covariance functions involving the boundary

$$k_{b,u}^{n,n} = \mathcal{B}_x k_{u,u}^{n,n}, \quad k_{b,b}^{n,n} = \mathcal{B}_x \mathcal{B}_{x'} k_{u,u}^{n,n}, \quad k_{b,u}^{n,n-j} = \mathcal{B}_x k_{u,u}^{n,n-j}, \quad j = 1, \dots, m.$$

The numerical examples accompanying this manuscript are designed to show-case different special treatments of boundary conditions, including Dirichlet, Neumann, mixed, and periodic boundary conditions.

## 2.2. Work flow and computational cost

The proposed work flow is summarized below:

- 1. Starting from the initial data  $\{x^0, u^0\}$  and the boundary data  $\{x_b^1, u_b^1\}$ , we train the kernel hyper-parameters as outlined in section 2.3. This step carries the main computational burden as it scales cubically with the total number of training points since it involves Cholesky factorization of full symmetric positive-definite covariance matrices [14].
- 2. Having identified the optimal set of kernel hyper-parameters, we utilize the conditional posterior distribution to predict the solution at the next time-step and generate the artificial data  $\{x^1, u^1\}$ . Note that  $x^1$  is randomly sampled in the spatial domain according to a uniform distribution, and  $u^1$  is a normally distributed random vector, as outlined in section 2.4.
- 3. Given the artificial data  $\{\boldsymbol{x}^1, \boldsymbol{u}^1\}$  and boundary data  $\{\boldsymbol{x}_b^2, \boldsymbol{u}_b^2\}$  we proceed with training the kernel hyper-parameters for the second timestep<sup>2</sup> (see section 2.3).
- 4. Having identified the optimal set of kernel hyper-parameters, we utilize the conditional posterior distribution to predict the solution at the

<sup>&</sup>lt;sup>2</sup>To be precise, we are using the mean of the random vector  $u^1$  for training purposes.

next time-step and generate the artificial data  $\{x^2, u^2\}$ , where  $x^2$  is randomly sampled in the spatial domain according to a uniform distribution. However, since  $u^1$  is a random vector, we have to marginalize it out in order to obtain consistent uncertainty estimates for  $u^2$ . This procedure is outlined in section 2.5.

5. Steps 3 and 4 are repeated until the final integration time is reached.

In summary, the proposed methodology boils down to a sequence of Gaussian process regressions at every time-step. To accelerate training, one can use the optimal set of hyper-parameters from the previous time-step as an initial guess for the current one.

#### 2.3. Training

In the following, for notational convenience and without loss of generality<sup>3</sup>, we will operate under the assumption that m = 1 (see equation (5)). The hyper-parameters  $\theta_i$ , i = 1, ..., m, can be trained by employing the Negative Log Marginal Likelihood resulting from

$$\begin{bmatrix} \boldsymbol{u}_b^n \\ \boldsymbol{u}^{n-1} \end{bmatrix} \sim \mathcal{N}\left(0, \boldsymbol{K}\right), \tag{12}$$

where  $\{\boldsymbol{x}_b^n, \boldsymbol{u}_b^n\}$  are the (noisy) data on the boundary,  $\{\boldsymbol{x}^{n-1}, \boldsymbol{u}^{n-1}\}$  are artificially generated data to be explained later (see equation (14)), and

$$\bm{K} := \left[ \begin{array}{cc} k_{b,b}^{n,n}(\bm{x}_b^n,\bm{x}_b^n) + \sigma_n^2 I & k_{b,u}^{n,n-1}(\bm{x}_b^n,\bm{x}^{n-1}) \ k_{u,u}^{n-1,n-1}(\bm{x}^{n-1},\bm{x}^{n-1}) + \sigma_{n-1}^2 I \end{array} \right].$$

It is worth mentioning that the marginal likelihood provides a natural regularization mechanism that balances the trade-off between data fit and model complexity. This effect is known as Occam's razor [26] after William of Occam 1285–1349 who encouraged simplicity in explanations by the principle: "plurality should not be assumed without necessity".

<sup>&</sup>lt;sup>3</sup>The reader should be able to figure out the details without much difficulty while generalizing to cases with m > 1. Moreover, for the examples accompanying this manuscript, more details are also provided in the appendix.

## 2.4. Posterior

In order to predict  $u^n(x_*^n)$  at a new test point  $x_*^n$ , we use the following conditional distribution

$$u^{n}(x_{*}^{n}) \mid \begin{bmatrix} \mathbf{u}_{b}^{n} \\ \mathbf{u}^{n-1} \end{bmatrix} \sim \mathcal{N}\left(\mathbf{q}^{T}\mathbf{K}^{-1} \begin{bmatrix} \mathbf{u}_{b}^{n} \\ \mathbf{u}^{n-1} \end{bmatrix}, k_{u,u}^{n,n}(x_{*}^{n}, x_{*}^{n}) - \mathbf{q}^{T}\mathbf{K}^{-1}\mathbf{q}\right),$$

where

$$\mathbf{q}^T := \left[ \begin{array}{cc} k_{u,b}^{n,n}(x_*^n, \mathbf{x}_b^n) & k_{u,u}^{n,n-1}(x_*^n, \mathbf{x}^{n-1}) \end{array} \right].$$

## 2.5. Propagating Uncertainty

However, to properly propagate the uncertainty associated with the initial data through time, one should not stop here. Since  $\{x^{n-1}, u^{n-1}\}$  are artificially generated data (see equation (14)) we have to marginalize them out by employing

$$\boldsymbol{u}^{n-1} \sim \mathcal{N}\left(\boldsymbol{\mu}^{n-1}, \boldsymbol{\Sigma}^{n-1,n-1}\right),$$

to obtain

$$u^{n}(x_{*}^{n}) \mid \boldsymbol{u}_{b}^{n} \sim \mathcal{N}\left(\mu^{n}(x_{*}^{n}), \Sigma^{n,n}(x_{*}^{n}, x_{*}^{n})\right),$$
 (13)

where

$$\mu^n(x_*^n) = \boldsymbol{q}^T \boldsymbol{K}^{-1} \left[ \begin{array}{c} \boldsymbol{u}_b^n \ \boldsymbol{\mu}^{n-1} \end{array} \right],$$

and

$$\Sigma^{n,n}(x_*^n, x_*^n) = k_{u,u}^{n,n}(x_*^n, x_*^n) - \mathbf{q}^T \mathbf{K}^{-1} \mathbf{q} + \mathbf{q}^T \mathbf{K}^{-1} \begin{bmatrix} 0 & 0 \\ 0 & \mathbf{\Sigma}^{n-1,n-1} \end{bmatrix} \mathbf{K}^{-1} \mathbf{q}.$$

Now, one can use the resulting posterior distribution (13) to obtain the artificially generated data  $\{x^n, u^n\}$  for the next time step with

$$\boldsymbol{u}^n \sim \mathcal{N}\left(\boldsymbol{\mu}^n, \boldsymbol{\Sigma}^{n,n}\right).$$
 (14)

Here,  $\boldsymbol{\mu}^n = \mu^n(\boldsymbol{x}^n)$  and  $\boldsymbol{\Sigma}^{n,n} = \Sigma^{n,n}(\boldsymbol{x}^n, \boldsymbol{x}^n)$ .

## 2.6. Example: Burgers' equation (Backward Euler)

Burgers' equation is a fundamental partial differential equation arising in various areas of applied mathematics, including fluid mechanics, nonlinear acoustics, gas dynamics, and traffic flow [27]. In one space dimension the equation reads as

$$u_t + uu_x = \nu u_{xx},\tag{15}$$

along with Dirichlet boundary conditions u(t, -1) = u(t, 1) = 0, where u(t, x) denotes the unknown solution and  $\nu$  is a viscosity parameter. Let us assume that all we observe are noisy measurements  $\{x^0, u^0\}$  of the black-box initial function  $u(0, x) = -\sin(\pi x)$ . Given such measurements, we would like to solve the Burgers' equation (15) while propagating through time the uncertainty associate with the noisy initial data (see figure 1). This example is important because it involves solving a non-linear partial differential equation. To illustrate how one can encode the structure of the physical laws expressed by Burgers' equation in a numerical Gaussian process let us apply the backward Euler scheme to equation (15). This can be written as

$$u^{n} = u^{n-1} - \Delta t u^{n} \frac{d}{dx} u^{n} + \nu \Delta t \frac{d^{2}}{dx^{2}} u^{n}. \tag{16}$$

We would like to place a Gaussian process prior on  $u^n$ . However, the non-linear term  $u^n \frac{d}{dx} u^n$  is causing problems simply because the product of two Gaussian processes is no longer Gaussian. Hence, we will approximate the nonlinear term with  $\mu^{n-1} \frac{d}{dx} u^n$ , where  $\mu^{n-1}$  is the posterior mean of the previous time step. Therefore, the backward Euler scheme (16) can be approximated by

$$u^{n} = u^{n-1} - \Delta t \mu^{n-1} \frac{d}{dx} u^{n} + \nu \Delta t \frac{d^{2}}{dx^{2}} u^{n}.$$
 (17)

Rearranging the terms, we obtain

$$u^{n} + \Delta t \mu^{n-1} \frac{d}{dr} u^{n} - \nu \Delta t \frac{d^{2}}{dr^{2}} u^{n} = u^{n-1}.$$
 (18)

#### 2.6.1. Numerical Gaussian Process

Let us make the prior assumption that

$$u^n(x) \sim \mathcal{GP}(0, k(x, x'; \theta)),$$
 (19)

![](_page_10_Figure_0.jpeg)

Figure 1: Burgers' equation: Initial data along with the posterior distribution of the solution at different time snapshots. The blue solid line represents the true data generating solution, while the dashed red line depicts the posterior mean. The shaded orange region illustrates the two standard deviations band around the mean. We are employing the backward Euler scheme with time step size  $\Delta t=0.01$ . At each time step we generate 31 artificial data points randomly located in the interval [-1,1] according to a uniform distribution. These locations are highlighted by the ticks along the horizontal axis. Here, we set  $\nu=0.01/\pi$  – a value leading to the development of a non singular thin internal layer at x=0 that is notoriously hard to resolve by classical numerical methods [27]. (Code: http://bit.ly/2mnUiKT, Movie: http://bit.ly/2m1SKHw)

is a Gaussian process with a neural network [14] covariance function

$$k(x, x'; \theta) = \frac{2}{\pi} \sin^{-1} \left( \frac{2(\sigma_0^2 + \sigma^2 x x')}{\sqrt{(1 + 2(\sigma_0^2 + \sigma^2 x^2))(1 + 2(\sigma_0^2 + \sigma^2 x'^2))}} \right), \quad (20)$$

where  $\theta = (\sigma_0^2, \sigma^2)$  denotes the hyper-parameters. Here we have chosen a non-stationary prior motivated by the fact that the solution to the Burgers' equation can develop discontinuities for small values of the viscosity parameter  $\nu$ . This enables us to obtain the following *Numerical Gaussian Process* 

$$\begin{bmatrix} u^n \\ u^{n-1} \end{bmatrix} \sim \mathcal{GP} \left( 0, \begin{bmatrix} k_{u,u}^{n,n} & k_{u,u}^{n,n-1} \\ & k_{u,u}^{n-1,n-1} \end{bmatrix} \right),$$

with covariance functions  $k_{u,u}^{n,n}$ ,  $k_{u,u}^{n,n-1}$ , and  $k_{u,u}^{n-1,n-1}$  given in section 5.1 of the appendix. Training, prediction, and propagating the uncertainty associated with the noisy initial observations can be performed as in sections 2.3, 2.4, and 2.5, respectively. Figure 1 depicts the noisy initial data along with the posterior distribution of the solution to the Burgers' equation (15) at different time snapshots. It is remarkable that the proposed methodology can effectively propagate an infinite collection of correlated Gaussian random variables (i.e., a Gaussian process) through the complex nonlinear dynamics of the Burgers' equation.

#### 2.6.2. Numerical Study

It must be re-emphasized that numerical Gaussian processes, by construction, are designed to deal with cases where: (1) all we observe is noisy data on black-box initial conditions, and (2) we are interested in quantifying the uncertainty associated with such noisy data in our solutions to time-dependent partial differential equations. In fact, we recommend resorting to other alternative classical numerical methods such as Finite Differences, Finite Elements, and Spectral methods in cases where: (1) the initial function is not a black-box function and we have access to noiseless data, or (2) we are not interested in quantifying the uncertainty in our solutions. However, in order to be able to perform a systematic numerical study of the proposed methodology and despite the fact that this defeats the whole purpose of the current work, sometimes we will operate under the assumption that we have access to noiseless initial data. For instance, concerning the Burgers' equation, if we had access to such noiseless data, we would obtain results similar

to the ones reported in figure 2. Moreover, in order to make sure that the numerical Gaussian process resulting from the backward Euler scheme (18) applied to the Burgers' equation is indeed first-order accurate in time, we perform the numerical experiments reported in figures 3 and 4. Specifically, in figure 3 we report the time-evolution of the relative spatial  $\mathcal{L}^2$  error until the final integration time T = 1.0. We observe that the error indeed grows as  $\mathcal{O}(\Delta t)$ , and its resulting behavior reveals both the shock development region as well as the energy dissipation due to diffusion at later times. Moreover, in figure 4 we fix the final integration time to T=0.1 and the number of initial and artificial data to 50, and vary the time-step size  $\Delta t$  from  $10^{-1}$  to  $10^{-4}$ . As expected, we recover the first-order convergence properties of the backward Euler scheme, except for a saturation region arising when we further reduce the time-step size below approximately  $10^{-3}$ . This behavior is not a result of the time stepping scheme but is attributed to the underlying Gaussian process regression and the finite number of spatial data points used for training and prediction. To investigate the accuracy of the posterior mean in predicting the solution as the number of training points is increased, we perform the numerical experiment reported in figure 5. Here we have considered two cases for which we fix the time step size to  $\Delta t = 10^{-2}$  and  $\Delta t = 10^{-3}$ , respectively, and increase the number of initial as well as artificial data points. A similar accuracy saturation is also observed here as the number of training points is increased. In this case, this is attributed to the error accumulated due to time-stepping with the relatively large time step sizes for the first-order accurate Euler scheme. If we further keep decreasing the time-step, this saturation behavior will occur for higher numbers of total training points. The key point here is that although Gaussian processes can yield satisfactory accuracy, they, by construction, cannot force the approximation error down to machine precision. This is due to the fact that Gaussian processes are suitable for solving regression problems. This is exactly the reason why we recommend other alternative classical numerical methods for solving partial differential equations in cases where one has access to noiseless data. In such cases, it is desirable to use numerical schemes that are capable of performing exact interpolation on the data, rather than just a mere regression.

#### 2.7. Example: Wave Equation (Trapezoidal Rule)

The wave equation is an important second-order linear partial differential equation for the description of wave propagation phenomena, including sound waves, light waves, and water waves. It arises in many scientific fields such

![](_page_13_Figure_0.jpeg)

Figure 2: Burgers' equation: Initial data along with the posterior distribution of the solution at different time snapshots. The blue solid line represents the true data generating solution, while the dashed red line depicts the posterior mean. The shaded orange region illustrates the two standard deviations band around the mean. We are employing the backward Euler scheme with time step size  $\Delta t = 0.01$ . At each time step we generate 101 artificial data points randomly located in the interval [-1,1] according to a uniform distribution. These locations are highlighted by the ticks along the horizontal axis. Here, we set  $\nu = 0.01/\pi$  – a value leading to the development of a non singular thin internal layer at x = 0 that is notoriously hard to resolve by classical numerical methods [27]. We are reporting the relative  $\mathcal{L}^2$ -error between the posterior mean and the true solution. (Code: http://bit.ly/2mDKCwb, Movie: http://bit.ly/2mDOPA5)

![](_page_14_Figure_0.jpeg)

Figure 3: Burgers' equation: Time evolution of the relative spatial  $\mathcal{L}^2$ -error up to the final integration time T=1.0. We are using the backward Euler scheme with a time step-size of  $\Delta t=0.01$ , and the red dashed line illustrates the optimal first-order convergence rate. (Code: http://bit.ly/2mDY6It)

![](_page_14_Figure_2.jpeg)

![](_page_14_Figure_3.jpeg)

Figure 4: Burgers' equation: Relative spatial  $\mathcal{L}^2$ -error versus step-size for the backward Euler scheme at time T=0.1. The number of noiseless initial and artificially generated data is set to be equal to 50. (Code: http://bit.ly/2mDY6It)

Figure 5: Burgers' equation: Relative spatial  $\mathcal{L}^2$ -error versus the number of noiseless initial as well as artificial data points used for the backward Euler scheme with time step-sizes of  $\Delta t = 10^{-2}$  and  $\Delta t = 10^{-3}$ . (Code: http://bit.ly/2mDY6It)

as acoustics, electromagnetics, and fluid dynamics. In one space dimension the wave equation reads as

$$u_{tt} = u_{xx}. (21)$$

The function  $u(t,x) = \frac{1}{2}\sin(\pi x)\cos(\pi t) + \frac{1}{3}\sin(3\pi x)\sin(3\pi t)$  solves this equation and satisfies the following initial and homogeneous Dirichlet boundary conditions

$$u(0,x) = u^{0}(x) := \frac{1}{2}\sin(\pi x),$$
  

$$u_{t}(0,x) = v^{0}(x) := \pi\sin(3\pi x),$$
  

$$u(t,0) = u(t,1) = 0.$$
(22)

Now, let us assume that all we observe are noisy measurements  $\{\boldsymbol{x}_{u}^{0}, \boldsymbol{u}^{0}\}$  and  $\{\boldsymbol{x}_{v}^{0}, \boldsymbol{v}^{0}\}$  of the *black-box* initial functions  $u^{0}$  and  $v^{0}$ , respectively. Given this data, we are interested in solving the wave equation (21) and quantifying the uncertainty in our solution associated with the noisy initial data (see figure 6). To proceed, let us define  $v := u_{t}$  and rewrite the wave equation as a system of equations given by

$$\begin{cases}
 u_t = v, \\
 v_t = u_{xx}.
\end{cases}$$
(23)

This example is important because it involves solving a *system* of partial differential equations. One could rewrite the system of equations (23) in matrix-vector notations and obtain

$$\frac{\partial}{\partial t} \left[ \begin{array}{c} u \\ v \end{array} \right] = \mathcal{L}_x \left[ \begin{array}{c} u \\ v \end{array} \right],$$

which takes the form of (1) with

$$\mathcal{L}_x = \left[ \begin{array}{cc} 0 & I \\ \frac{\partial^2}{\partial x^2} & 0 \end{array} \right].$$

This form is now amenable to the previous analysis provided for general linear multi-step methods. However, for pedagogical purposes, let us walk slowly through the trapezoidal rule and apply it to the system of equations

![](_page_16_Figure_0.jpeg)

Figure 6: Wave equation: Initial data along with the posterior distribution of the solution at different time snapshots. Here,  $v(t,x)=u_t(t,x)$ . The blue solid line represents the true data generating solution, while the dashed red line depicts the posterior mean. The shaded orange region illustrates the two standard deviations band around the mean. At each time step we generate 51 artificial data points for u and 49 for v, all randomly located in the interval [0,1] according to a uniform distribution. These locations are highlighted by the ticks along the horizontal axis. We are employing the trapezoidal scheme with time step size  $\Delta t = 0.01$ . (Code: http://bit.ly/2m9fhNi)

(23). This can be written as

$$u^{n} = u^{n-1} + \frac{1}{2}\Delta t v^{n-1} + \frac{1}{2}\Delta t v^{n},$$

$$v^{n} = v^{n-1} + \frac{1}{2}\Delta t \frac{d^{2}}{dx^{2}}u^{n-1} + \frac{1}{2}\Delta t \frac{d^{2}}{dx^{2}}u^{n}.$$
(24)

Rearranging the terms yields

$$u^{n} - \frac{1}{2}\Delta t v^{n} = u^{n-1} + \frac{1}{2}\Delta t v^{n-1},$$
  
$$v^{n} - \frac{1}{2}\Delta t \frac{d^{2}}{dx^{2}} u^{n} = v^{n-1} + \frac{1}{2}\Delta t \frac{d^{2}}{dx^{2}} u^{n-1}.$$

Now, let us define  $u^{n-1/2}$  and  $v^{n-1/2}$  to be given by

$$u^{n} - \frac{1}{2}\Delta t v^{n} =: u^{n-1/2} := u^{n-1} + \frac{1}{2}\Delta t v^{n-1},$$

$$v^{n} - \frac{1}{2}\Delta t \frac{d^{2}}{dx^{2}} u^{n} =: v^{n-1/2} := v^{n-1} + \frac{1}{2}\Delta t \frac{d^{2}}{dx^{2}} u^{n-1}.$$
(25)

As outlined in section 2 this is a key step in the proposed methodology as it hints at the proper location to place the Gaussian process prior. Shifting the terms involved in the above equations by -1/2 and +1/2 we obtain

$$u^{n-1/2} - \frac{1}{2}\Delta t v^{n-1/2} = u^{n-1},$$

$$v^{n-1/2} - \frac{1}{2}\Delta t \frac{d^2}{dx^2} u^{n-1/2} = v^{n-1},$$
(26)

and

$$u^{n} = u^{n-1/2} + \frac{1}{2}\Delta t v^{n-1/2},$$

$$v^{n} = v^{n-1/2} + \frac{1}{2}\Delta t \frac{d^{2}}{dx^{2}} u^{n-1/2},$$
(27)

respectively. Now we can proceed with encoding the structure of the wave equation into a numerical Gaussian process prior for performing Bayesian machine learning of the solution  $\{u(t, x), v(t, x)\}$  at any t > 0.

#### 2.7.1. Numerical Gaussian Process

Let us make the prior assumption that

$$u^{n-1/2}(x) \sim \mathcal{GP}(0, k_u(x, x'; \theta_u)),$$

$$v^{n-1/2}(x) \sim \mathcal{GP}(0, k_v(x, x'; \theta_v)),$$
(28)

are two independent Gaussian processes with squared exponential [14] covariance functions

$$k_u(x, x'; \theta_u) = \gamma_u^2 \exp\left(-\frac{1}{2}w_u(x - x')^2\right),$$

$$k_v(x, x'; \theta_v) = \gamma_v^2 \exp\left(-\frac{1}{2}w_v(x - x')^2\right),$$
(29)

where  $\theta_u = (\gamma_u^2, w_u)$  and  $\theta_v = (\gamma_v^2, w_v)$ . From a theoretical point of view, each covariance function gives rise to a Reproducing Kernel Hilbert space [28, 29, 30] that defines a class of functions that can be represented by this kernel. In particular, the squared exponential covariance function chosen above implies smooth approximations. More complex function classes can be accommodated by appropriately choosing kernels (see e.g., equation (20)). This enables us to obtain the following numerical Gaussian process

$$\begin{bmatrix} u^{n} \\ v^{n} \\ u^{n-1} \\ v^{n-1} \end{bmatrix} \sim \mathcal{GP} \left( 0, \begin{bmatrix} k_{u,u}^{n,n} & k_{u,v}^{n,n} & k_{u,u}^{n,n-1} & k_{u,v}^{n,n-1} \\ k_{v,v}^{n,n} & k_{v,u}^{n,n-1} & k_{v,v}^{n,n-1} \\ k_{u,u}^{n-1,n-1} & k_{u,v}^{n-1,n-1} \\ k_{v,v}^{n-1,n-1} & k_{v,v}^{n-1,n-1} \end{bmatrix} \right),$$

which captures the entire structure of the trapezoidal rule (24), applied to the wave equation (21), in its covariance functions given in section 5.2 of the appendix. Training, prediction, and propagating the uncertainty associated with the noisy initial observations can be performed as in section 5.2 of the appendix. Figure 6 depicts the noisy initial data along with the posterior distribution (50) of the solution to the wave equation (21) at different time snapshots.

#### 2.7.2. Numerical Study

In the case where we have access to noiseless initial data we obtain the results depicted in figure 7. Moreover, we perform a numerical study similar to the one reported in section 2.6.2. This is to verify that the *numerical* 

![](_page_19_Figure_0.jpeg)

Figure 7: Wave equation: Initial data along with the posterior distribution of the solution at different time snapshots. Here,  $v(t,x) = u_t(t,x)$ . The blue solid line represents the true data generating solution, while the dashed red line depicts the posterior mean. The shaded orange region illustrates the two standard deviations band around the mean. At each time step we generate 51 artificial data points for u and 49 for v, all randomly located in the interval [0,1] according to a uniform distribution. These locations are highlighted by the ticks along the horizontal axis. We are employing the trapezoidal scheme with time step size  $\Delta t = 0.01$ . We are reporting the relative  $\mathcal{L}^2$ -error between the posterior mean and the true solution. (Code: http://bit.ly/2m3mKhK, Movie: http://bit.ly/2mFalVg)

Gaussian process resulting from the trapezoidal rule (24) applied to the wave equation is indeed second-order accurate in time. In particular, the numerical experiment shown in figure 8 illustrates the time evolution of the relative spatial  $\mathcal{L}^2$  until the final integration time T=1.5. The second-order convergence of the algorithm is also demonstrated in figure 9 where we have fixed the number of noiseless initial and artificially generated data, while decreasing the time step size. We also investigate the convergence behavior of the algorithm for a fixed time-step  $\Delta t = 10^{-2}$  and as the number of training points is increased. The results are summarized in figure 10. The analysis of both temporal and spatial convergence properties yield qualitatively similar conclusions to the ones reported in section 2.6.2. One thing worth mentioning here is that the error in u is not always less than the error in v (as seen in figures 7 and 8). This just happens to be the case at time T = 0.2.

## 3. Runge-Kutta Methods

Let us now focus on the general form of Runge-Kutta methods [31] with q stages applied to equation (1); i.e.,

$$u^{n+1} = u^{n} + \Delta t \sum_{i=1}^{q} b_{i} \mathcal{L}_{x} u^{n+\tau_{i}},$$

$$u^{n+\tau_{i}} = u^{n} + \Delta t \sum_{i=1}^{q} a_{ij} \mathcal{L}_{x} u^{n+\tau_{j}}, \quad i = 1, \dots, q.$$
(30)

Here,  $u^{n+\tau_i}(x) = u(t^n + \tau_i \Delta t, x)$ . This general form encapsulates both implicit and explicit time-stepping schemes, depending on the choice of the weights  $\{a_{ij}, b_i\}$ . An important feature of the proposed methodology is that it is oblivious to the choice of these parameters, hence the implicit or explicit nature of the time-stepping scheme is ultimately irrelevant. This is in sharp contrast to classical numerical methods in which implicit time-integration is burdensome due to the need for repeatedly solving linear or nonlinear systems. Here, for a fixed number of stages q, the cost of performing implicit or explicit time-marching is identical. This is attributed to the fact that the structure of the time-stepping scheme is encoded in the numerical Gaussian process prior, and the algorithm only involves solving a sequence of regression problems as outlined in section 2.2. This allows us to enjoy the favorable stability properties of fully implicit schemes at no extra cost, and thus per-

![](_page_21_Figure_0.jpeg)

Figure 8: Wave equation: Time evolution of the relative spatial  $\mathcal{L}^2$ -error up to the final integration time T=1.5. The blue solid line corresponds to the u component of the solution while the black dashed line corresponds to the function v. We are using the trapezoidal rule with a time step-size of  $\Delta t=0.01$ , and the red dashed line illustrates the optimal second-order convergence rate. (Code: http://bit.ly/2niW6lW)

![](_page_21_Figure_2.jpeg)

Time: 0.2  $10^{-1}$   $10^{-2}$   $10^{-3}$  4 6 8 10 12 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10 10

Figure 9: Wave equation: Relative spatial  $\mathcal{L}^2$ -error versus step-size for the trapezoidal rule. Here, the number of noiseless initial data as well as the artificially generated data is set to be equal to 50. We are running the time stepping scheme up until time 0.2. (Code: http://bit.ly/2niW6lW)

Figure 10: Wave equation: Relative spatial  $\mathcal{L}^2$ -error versus the number of noiseless initial as well as artificial data points used for the trapezoidal rule. Here, the time stepsize is set to be  $\Delta t = 0.01$ . We are running the time stepping scheme up until time 0.2. (Code: http://bit.ly/2niW6lW)

form long-time integration using very large time-steps. Equations (30) can be equivalently written as

$$u^{n+1} - \Delta t \sum_{i=1}^{q} b_i \mathcal{L}_x u^{n+\tau_i} = u^n =: u_{q+1}^n,$$

$$u^{n+\tau_i} - \Delta t \sum_{j=1}^{q} a_{ij} \mathcal{L}_x u^{n+\tau_j} = u^n =: u_i^n, \quad i = 1, \dots, q.$$
(31)

Let us make the prior assumption that

$$u^{n+1}(x) \sim \mathcal{GP}(0, k_{u,u}^{n+1,n+1}(x, x'; \theta_{n+1})),$$

$$u^{n+\tau_i}(x) \sim \mathcal{GP}(0, k_{u,u}^{n+\tau_i, n+\tau_i}(x, x'; \theta_{n+\tau_i})), \quad i = 1, \dots, q,$$
(32)

are q+1 mutually independent Gaussian processes. Therefore, we can write the joint distribution of  $u^{n+1}, u^{n+\tau_q}, \ldots, u^{n+\tau_1}, u^n_{q+1}, \ldots, u^n_1$  which will capture the entire structure of the Runge-Kutta methods in the resulting numerical Gaussian process. However, rather than getting bogged down into heavy notation, and without sacrificing any generality, we will present the main ideas through the lens of an example.

# 3.1. Example: Advection Equation (Gauss-Legendre Method)

We have chosen this classical pedagogical example as a prototype benchmark problem for testing the limits of long-time integration. This example also highlights the implementation of periodic constraints at the domain boundaries (34). The advection equation in one space dimension takes the form

$$u_t = -u_x. (33)$$

The function  $u(t,x) = \sin(2\pi(x-t))$  solves this equation and satisfies the following initial and periodic boundary conditions

$$u(0,x) = u^{0}(x) := \sin(2\pi x),$$
  
 $u(t,0) = u(t,1).$  (34)

However, let us assume that all we observe are noisy measurements  $\{x^0, u^0\}$  of the *black-box* initial function  $u^0$ . Given this data, we are interested in encoding the structure of the advection operator in a *numerical Gaussian pro-*

cess prior and use it to infer the solution u(t, x) with quantified uncertainty for any t > 0 (see figure 11). Let us apply the Gauss-Legendre time-stepping quadrature [32] with two stages (thus fourth-order accurate) to the advection equation (33). Referring to equations (31), we obtain

$$u_{3}^{n} := u^{n} = u^{n+1} + b_{1} \Delta t \frac{d}{dx} u^{n+\tau_{1}} + b_{2} \Delta t \frac{d}{dx} u^{n+\tau_{2}},$$

$$u_{2}^{n} := u^{n} = u^{n+\tau_{2}} + a_{21} \Delta t \frac{d}{dx} u^{n+\tau_{1}} + a_{22} \Delta t \frac{d}{dx} u^{n+\tau_{2}},$$

$$u_{1}^{n} := u^{n} = u^{n+\tau_{1}} + a_{11} \Delta t \frac{d}{dx} u^{n+\tau_{1}} + a_{12} \Delta t \frac{d}{dx} u^{n+\tau_{2}}.$$

$$(35)$$

Here, 
$$\tau_1 = \frac{1}{2} - \frac{1}{6}\sqrt{3}$$
,  $\tau_2 = \frac{1}{2} + \frac{1}{6}\sqrt{3}$ ,  $b_1 = b_2 = \frac{1}{2}$ ,  $a_{11} = a_{22} = \frac{1}{4}$ ,  $a_{12} = \frac{1}{4} - \frac{1}{6}\sqrt{3}$ , and  $a_{21} = \frac{1}{4} + \frac{1}{6}\sqrt{3}$ .

## 3.1.1. Prior

We make the prior assumption that

$$u^{n+1}(x) \sim \mathcal{GP}(0, k_{u,u}^{n+1,n+1}(x, x'; \theta_{n+1})),$$

$$u^{n+\tau_2}(x) \sim \mathcal{GP}(0, k_{u,u}^{n+\tau_2, n+\tau_2}(x, x'; \theta_{n+\tau_2})),$$

$$u^{n+\tau_1}(x) \sim \mathcal{GP}(0, k_{u,u}^{n+\tau_1, n+\tau_1}(x, x'; \theta_{n+\tau_1})),$$
(36)

are three independent Gaussian processes with squared exponential covariance functions similar to the kernels used in equations (29). This assumption yields the following numerical Gaussian process

$$\begin{bmatrix} u^{n+1} \\ u^{n+\tau_2} \\ u^{n+\tau_1} \\ u^n_3 \\ u^n_1 \end{bmatrix} \sim \mathcal{GP} \left( 0, \begin{bmatrix} k^{n+1,n+1} & 0 & 0 & k^{n+1,n}_{u,3} & 0 & 0 \\ k^{n+\tau_2,n+\tau_2} & 0 & k^{n+\tau_2,n}_{u,3} & k^{n+\tau_2,n}_{u,2} & k^{n+\tau_2,n}_{u,1} \\ k^{n+\tau_1,n+\tau_1} & k^{n+\tau_1,n+\tau_1}_{u,3} & k^{n+\tau_1,n}_{u,3} & k^{n+\tau_1,n}_{u,2} & k^{n+\tau_1,n}_{u,1} \\ k^{n+\tau_1,n+\tau_1} & k^{n+\tau_1,n+\tau_1}_{u,3} & k^{n,n}_{3,3} & k^{n,n}_{3,2} & k^{n,n}_{3,1} \\ k^{n,n}_{3,3} & k^{n,n}_{3,2} & k^{n,n}_{2,1} \\ k^{n,n}_{1,1} & k^{n,n}_{1,1} \end{bmatrix} \right),$$

where the covariance functions are given in section 5.3 of the appendix.

![](_page_24_Figure_0.jpeg)

Figure 11: Advection equation: Initial data along with the posterior distribution of the solution at different time snapshots. The blue solid line represents the true data generating solution, while the dashed red line depicts the posterior mean. The shaded orange region illustrates the two standard deviations band around the mean. At each time step we generate 25 artificial data points randomly located in the interval [0,1] according to a uniform distribution. These locations are highlighted by the ticks along the horizontal axis. We are employing the Gauss-Legendre time-stepping quadrature rule with time step size  $\Delta t = 0.1$ . It is worth highlighting that we are running the time stepping scheme for a very long time and with a relatively large time step size. (Code: http://bit.ly/2m3JoXb, Movie: http://bit.ly/2mKHCP4)

#### 3.1.2. Training

The hyper-parameters  $\theta_{n+1}$ ,  $\theta_{n+\tau_2}$ , and  $\theta_{n+\tau_1}$  can be trained by minimizing the Negative Log Marginal Likelihood resulting from

$$\begin{bmatrix} u^{n+1}(1) - u^{n+1}(0) \\ u^{n+\tau_2}(1) - u^{n+\tau_2}(0) \\ u^{n+\tau_1}(1) - u^{n+\tau_1}(0) \\ \mathbf{u}_3^n \\ \mathbf{u}_2^n \\ \mathbf{u}_1^n \end{bmatrix} \sim \mathcal{N}(0, \mathbf{K}).$$
(37)

Here,  $u^{n+1}(1) - u^{n+1}(0) = 0$ ,  $u^{n+\tau_2}(1) - u^{n+\tau_2}(0) = 0$ , and  $u^{n+\tau_1}(1) - u^{n+\tau_1}(0) = 0$  correspond to the periodic boundary condition (34). Moreover,  $\boldsymbol{u}_3^n = \boldsymbol{u}_2^n = \boldsymbol{u}_1^n = \boldsymbol{u}^n$  and  $\{\boldsymbol{x}^n, \boldsymbol{u}^n\}$  are the artificially generated data. This last equality reveals a key feature of this Runge-Kutta numerical Gaussian process, namely the fact that it inspects the same data through the lens of different kernels. A detailed derivation of the covariance matrix  $\boldsymbol{K}$  is given in section 5.3 of the appendix. Prediction and propagation of uncertainty associated with the noisy initial observations can be performed as in section 5.3 of the appendix. Figure 11 depicts the noisy initial data along with the posterior distribution (52) of the solution to the advection equation (33) at different time snapshots.

## 3.1.3. Numerical Study

In the case where we have access to noiseless initial data we obtain the results depicted in figure 12. Moreover, in order to make sure that the *numerical Gaussian process* resulting from the Gauss-Legendre method (35) applied to the advection equation is indeed fourth-order accurate in time, we perform the numerical experiment reported in figures 13 and 14. The qualitative analysis of the temporal as well as the spatial convergence properties (as seen in figure 15) closely follows the conclusions drawn in section 2.6.2.

#### 3.2. Example: Heat Equation (Trapezoidal Rule)

Revisiting the trapezoidal rule, equipped with the machinery introduced for the Runge-Kutta methods, we obtain an alternative numerical Gaussian process to the one proposed in section 2. We will apply the resulting scheme to the heat equation in two space dimensions; i.e.,

$$u_t = u_{x_1x_1} + u_{x_2x_2}, \quad x_1 \in [0, 1], \ x_2 \in [0, 1].$$
 (38)

![](_page_26_Figure_0.jpeg)

Figure 12: Advection equation: Initial data along with the posterior distribution of the solution at different time snapshots. The blue solid line represents the true data generating solution, while the dashed red line depicts the posterior mean. The shaded orange region illustrates the two standard deviations band around the mean. At each time step we generate 25 artificial data points randomly located in the interval [0,1] according to a uniform distribution. These locations are highlighted by the ticks along the horizontal axis. We are employing the Gauss-Legendre time-stepping quadrature with time step size  $\Delta t = 0.1$ . It is worth highlighting that we are running the time stepping scheme for a very long time with a relatively large time step size. We are reporting the relative spatial  $\mathcal{L}^2$ -error between the posterior mean and the true solution. (Code: http://bit.ly/2mp0tfQ, Movie: http://bit.ly/2mp0tfQ,

![](_page_27_Figure_0.jpeg)

Figure 13: Advection equation: Time evolution of the relative spatial  $\mathcal{L}^2$ -error up to the final integration time T=99.0. We are using the Gauss-Legendre implicit Runge-Kutta scheme with a time step-size of  $\Delta t=0.1$ . The red dashed line illustrates the optimal fourth-order convergence rate. (Code: http://bit.ly/2mntVDh)

![](_page_27_Figure_2.jpeg)

Time: 0.5

10<sup>-2</sup>

10<sup>-3</sup>

6 8 10 12 14

number of data points

Figure 14: Advection equation: Relative spatial  $\mathcal{L}^2$ -error versus step-size for the Gauss-Legendre method. Here, the number of noiseless initial data as well as the artificially generated data is set to be equal to 50. We are running the time stepping scheme up until time 0.5. (Code: http://bit.ly/2mntVDh)

Figure 15: Advection equation: Relative spatial  $\mathcal{L}^2$ -error versus the number of noiseless initial as well as artificial data points used for the Gauss-Legendre method. Here, the time step-size is set to be  $\Delta t = 0.1$ . We are running the time stepping scheme up until time 0.5. (Code: http://bit.ly/2mntVDh)

The function  $u(t, x_1, x_2) = e^{-\frac{5\pi^2 t}{4}} \sin(\pi x_1) \sin(\frac{\pi x_2}{2})$  solves this equation and satisfies the following initial and boundary conditions

$$u(0, x_1, x_2) = \sin(\pi x_1) \sin\left(\frac{\pi x_2}{2}\right),$$

$$u(t, 0, x_2) = u(t, 1, x_2) = 0, \quad u(t, x_1, 0) = 0,$$

$$u_{x_2}(t, x_1, 1) = 0.$$
(39)

Equations (39) involve Dirichlet boundary conditions while equation (40) corresponds to a Neumann-type boundary. Let us assume that all we observe are noisy measurements  $\{(\boldsymbol{x}_1^0, \boldsymbol{x}_2^0), \boldsymbol{u}^0\}$  of the black-box initial function  $u(0, x_1, x_2)$ . Given such measurements, we would like to infer the latent scalar field  $u(t, x_1, x_2)$  (i.e., the solution to the heat equation (38)), while quantifying the uncertainty associated with the noisy initial data (see figure 16). This example showcases the ability of the proposed methods to handle multi-dimensional spatial domains and mixed boundary conditions (see equations (39) and (40)). Let us apply the trapezoidal scheme to the heat equation (38). The trapezoidal rule for the heat equation is given by

$$u^{n+1} = u^{n} + \frac{1}{2}\Delta t \frac{d^{2}}{dx_{1}^{2}} u^{n} + \frac{1}{2}\Delta t \frac{d^{2}}{dx_{1}^{2}} u^{n+1}$$

$$+ \frac{1}{2}\Delta t \frac{d^{2}}{dx_{2}^{2}} u^{n} + \frac{1}{2}\Delta t \frac{d^{2}}{dx_{2}^{2}} u^{n+1}.$$

$$(41)$$

Rearranging the terms, we can write  $u_1^n := u^n$  and

$$u_{2}^{n} := u_{3}^{n} := u^{n} = u^{n+1} - \frac{1}{2} \Delta t \frac{d^{2}}{dx_{1}^{2}} u^{n} - \frac{1}{2} \Delta t \frac{d^{2}}{dx_{1}^{2}} u^{n+1}$$

$$- \frac{1}{2} \Delta t \frac{d^{2}}{dx_{2}^{2}} u^{n} - \frac{1}{2} \Delta t \frac{d^{2}}{dx_{2}^{2}} u^{n+1}.$$

$$(42)$$

In other words, we are just rewriting equations (35) for the heat equation (38) with  $\tau_1 = 0$ ,  $\tau_2 = 1$ ,  $b_1 = b_2 = \frac{1}{2}$ ,  $a_{11} = a_{12} = 0$ , and  $a_{21} = a_{22} = 1/2$ .

## 3.2.1. Prior

Similar to the strategy (32) adopted for the Runge-Kutta methods, and as an alternative to the scheme used in section 2, we make the following prior

![](_page_29_Figure_0.jpeg)

Figure 16: Heat equation: Initial data along with the posterior distribution of the solution at different time snapshots. The blue surface with solid lines represents the true data generating solution, while the red surface with dashed lines depicts the posterior mean. The two standard deviations band around the mean is depicted using the orange surface with dotted boundary. We are employing the trapezoidal rule with time step size  $\Delta t = 0.01$ . At each time step we generate 20 artificial data points randomly located in the domain  $[0,1] \times [0,1]$  according to a uniform distribution. We employ three noiseless data-points per boundary. (Code: http://bit.ly/2mnFpGS, Movie: http://bit.ly/2mq4UZt)

assumptions:

$$u^{n+1}(x_1, x_2) \sim \mathcal{GP}(0, k_{u,u}^{n+1,n+1}((x_1, x_2), (x_1', x_2'); \theta_{n+1})),$$

$$u^{n}(x_1, x_2) \sim \mathcal{GP}(0, k_{u,u}^{n,n}((x_1, x_2), (x_1', x_2'); \theta_n)).$$

$$(43)$$

Here, we employ anisotropic squared exponential covariance functions of the form

$$\begin{aligned} k_{u,u}^{n+1,n+1}((x_1,x_2),(x_1',x_2');\theta_{n+1}) \\ &= \gamma_{n+1}^2 \exp\left(-\frac{1}{2}w_{n+1,1}(x_1-x_1')^2 - \frac{1}{2}w_{n+1,2}(x_2-x_2')^2\right), \\ k_{u,u}^{n,n}((x_1,x_2),(x_1',x_2');\theta_n) \\ &= \gamma_n^2 \exp\left(-\frac{1}{2}w_{n,1}(x_1-x_1')^2 - \frac{1}{2}w_{n,2}(x_2-x_2')^2\right). \end{aligned}$$

The hyper-parameters are given by  $\theta_{n+1} = (\gamma_{n+1}^2, w_{n+1,1}, w_{n+1,2})$  and  $\theta_n = (\gamma_n^2, w_{n,1}, w_{n,2})$ . To deal with the mixed boundary conditions (39) and (40), let us define  $v^{n+1} := \frac{d}{dx_2}u^{n+1}$  and  $v^n := \frac{d}{dx_2}u^n$ . We obtain the following numerical Gaussian process

$$\begin{bmatrix} u^{n+1} \\ v^{n+1} \\ u^n \\ v^n \\ u^n_3 \\ u^n_1 \end{bmatrix} \sim \mathcal{GP} \left( 0, \begin{bmatrix} k_{u,u}^{n+1,n+1} & k_{u,v}^{n+1,n+1} & 0 & 0 & k_{u,3}^{n+1,n} & 0 \\ k_{v,v}^{n+1,n+1} & 0 & 0 & k_{v,3}^{n+1,n} & 0 \\ k_{v,v}^{n+1,n+1} & 0 & 0 & k_{v,3}^{n+1,n} & 0 \\ k_{v,v}^{n,n} & k_{u,v}^{n,n} & k_{u,3}^{n,n} & k_{u,1}^{n,n} \\ k_{v,v}^{n,n} & k_{v,v}^{n,n} & k_{v,3}^{n,n} & k_{v,1}^{n,n} \\ k_{v,v}^{n,n} & k_{u,3}^{n,n} & k_{u,1}^{n,n} \\ k_{1,1}^{n,n} \end{bmatrix} \right),$$

where the covariance functions are given in section 5.4 of the appendix.

#### 3.2.2. Training

The hyper-parameters  $\theta_{n+1}$  and  $\theta_n$  can be trained by minimizing the Negative Log Marginal Likelihood resulting from

$$\begin{bmatrix} \boldsymbol{u}_{D}^{n+1} \\ \boldsymbol{v}_{N}^{n+1} \\ \boldsymbol{u}_{D}^{n} \\ \boldsymbol{v}_{N}^{n} \\ \boldsymbol{u}_{3}^{n} \\ \boldsymbol{u}_{1}^{n} \end{bmatrix} \sim \mathcal{N}(0, \boldsymbol{K}), \tag{44}$$

where  $\{(\boldsymbol{x}_{1,D}^{n+1}, \boldsymbol{x}_{2,D}^{n+1}), \boldsymbol{u}_D^{n+1}\}$  and  $\{(\boldsymbol{x}_{1,D}^n, \boldsymbol{x}_{2,D}^n), \boldsymbol{u}_D^n\}$  denote the data on the Dirichlet (39) portion of the boundary, while

$$\{({\bm x}_{1,N}^{n+1},{\bm x}_{2,N}^{n+1}),{\bm u}_N^{n+1}\}$$
 and  $\{({\bm x}_{1,N}^n,{\bm x}_{2,N}^n),{\bm u}_N^n\}$ 

correspond to the Neumann (40) boundary data. Moreover,  $\mathbf{u}_1^n = \mathbf{u}_3^n = \mathbf{u}^n$  and  $\{(\mathbf{x}_1^n, \mathbf{x}_2^n), \mathbf{u}^n\}$  are the artificially generated data. The exact form of the covariance matrix  $\mathbf{K}$  is given in section 5.4 of the appendix. Prediction and propagation of uncertainty associated with the noisy initial observations can be performed as in section 5.4 of the appendix. Figure 16 depicts the noisy initial data along with the posterior distribution (57) of the solution to the Heat equation (38) at different time snapshots.

## 3.2.3. Numerical Study

In order to be able to perform a systematic numerical study of the proposed methodology, we will operate under the assumption that we have access to noiseless initial data. The corresponding results are reported in figure 17. Moreover, in order to make sure that the numerical Gaussian process resulting from the Runge-Kutta version of the trapezoidal rule (41) applied to the Heat equation is indeed second-order accurate in time, we perform the numerical experiments reported in figures 18 and 19. Again, the qualitative analysis of the temporal as well as the spatial convergence properties (as seen in figure 20) closely follows the conclusions drawn in section 2.6.2.

## 4. Concluding Remarks

We have presented a novel machine learning framework for encoding physical laws described by partial differential equations into Gaussian process

![](_page_32_Figure_0.jpeg)

Figure 17: Heat equation: Initial data along with the posterior distribution of the solution at different time snapshots. The blue surface with solid lines represents the true data generating solution, while the red surface with dashed lines depicts the posterior mean. The two standard deviations band around the mean is depicted using the orange surface with dotted boundary. We are employing the trapezoidal rule with time step size  $\Delta t = 0.01$ . At each time step we generate 20 artificial data points randomly located in the domain  $[0,1] \times [0,1]$  according to a uniform distribution. We employ three noiseless datapoints per boundary. We are reporting the relative  $\mathcal{L}^2$ -error between the posterior mean and the true solution. (Code: http://bit.ly/2mLwyB6, Movie: http://bit.ly/2mFRod)

![](_page_33_Figure_0.jpeg)

Figure 18: Heat equation: Time evolution of the relative spatial  $\mathcal{L}^2$ -error up to the final integration time T=0.2. We are using the trapezoidal rule with a time step-size of  $\Delta t=0.01$ , and the red dashed line illustrates the optimal second-order convergence rate. (Code: http://bit.ly/2m7aoG9)

![](_page_33_Figure_2.jpeg)

Figure 19: Heat equation: Relative spatial  $\mathcal{L}^2$ -error versus step-size for the Runge-Kutta version of the trapezoidal rule at time T=0.2. Here, the number of noiseless initial data as well as the artificially generated data is set to be equal to 50. We are running the time stepping scheme up until time 0.2. We employ 10 noiseless data per boundary. (Code: http://bit.ly/2m7aoG9)

![](_page_33_Figure_4.jpeg)

Figure 20: Heat equation: Relative spatial  $\mathcal{L}^2$ -error versus the number of noiseless initial as well as artificial data points used for the Runge-Kutta version of the trapezoidal rule at time T=0.2. Here, the time step-size is set to be  $\Delta t=0.01$ . We are running the time stepping scheme up until time 0.2. We employ 10 noiseless data per boundary. (Code: http://bit.ly/2m7aoG9)

priors for nonparametric Bayesian regression. The proposed algorithms can be used to infer solutions to time-dependent and nonlinear partial differential equations, and effectively quantify and propagate uncertainty due to noisy initial or boundary data. Moreover, to the best of our knowledge, this is the first attempt to construct structured learning machines which are explicitly informed by the underlying physics that possibly generated the observed data. Exploiting this structure is critical for constructing data-efficient learning algorithms that can effectively distill information in the data-scarce scenarios appearing routinely when we study complex physical systems.

In contrast to classical deterministic numerical methods for solving partial differential equations (e.g., finite difference and finite-element methods), the proposed approach is by construction capable of propagating entire probability distributions in time. Although this provides a natural platform for learning from noisy data and computing under uncertainty, it comes with a non-negligible computational cost. Specifically, a limitation of this work in its present form stems from the cubic scaling with respect to the total number of training data points. In future work we plan to design more computationally efficient algorithms by exploring ideas including recursive Kalman updates [33] and variational inference [34].

From a classical numerical analysis standpoint, it also becomes natural to ask questions on convergence, derivation of dispersion relations, quantification of truncation errors, comparison against classical schemes, etc. We must underline that these questions become obsolete in presence of noisy data and cannot be straightforwardly tackled using standard techniques from numerical analysis due to the probabilistic nature of the proposed work flow. In the realm of numerical Gaussian processes such questions translate into investigating theoretical concepts like prior consistency [14], posterior robustness [35], and posterior contraction rates [36]. These define a vast territory for analysis and future developments that currently remains unexplored.

In terms of future work, we plan to leverage the proposed framework to study more complex physical systems (e.g., fluid flows via the Navier-Stokes prior), propose extensions that can accommodate parameter inference, inverse and model discovery problems [13], as well as incorporate probabilistic time integration schemes that allow for a natural quantification of uncertainty due to time-stepping errors [37].

## Acknowledgements

This works received support by the DARPA EQUiPS grant N66001-15-2-4055, and the AFOSR grant 5210009.

#### References

#### References

- [1] A. Krizhevsky, I. Sutskever, G. E. Hinton, Imagenet classification with deep convolutional neural networks, in: Advances in neural information processing systems, pp. 1097–1105.
- [2] S. Hochreiter, J. Schmidhuber, Long short-term memory, Neural computation 9 (1997) 1735–1780.
- [3] Z. Ghahramani, Probabilistic machine learning and artificial intelligence, Nature 521 (2015) 452–459.
- [4] Y. LeCun, Y. Bengio, G. Hinton, Deep learning, Nature 521 (2015) 436–444.
- [5] M. Jordan, T. Mitchell, Machine learning: Trends, perspectives, and prospects, Science 349 (2015) 255–260.
- [6] Probabilistic numerics, http://probabilistic-numerics.org/index.html, 2017.
- [7] H. Poincaré, Calcul des probabilités, Gauthier-Villars, Paris, 1896.
- [8] P. Diaconis, Bayesian numerical analysis, Statistical decision theory and related topics IV 1 (1988) 163–175.
- [9] A. OHagan, Some Bayesian numerical analysis, Bayesian statistics 4 (1992) 4–2.
- [10] P. Hennig, M. A. Osborne, M. Girolami, Probabilistic numerics and uncertainty in computations, Proceedings of the Royal Society of London A: Mathematical, Physical and Engineering Sciences 471 (2015).
- [11] P. R. Conrad, M. Girolami, S. Särkkä, A. Stuart, K. Zygalakis, Statistical analysis of differential equations: introducing probability measures on numerical solutions, Statistics and Computing (2016) 1–18.

- [12] M. Raissi, P. Perdikaris, G. E. Karniadakis, Inferring solutions of differential equations using noisy multi-fidelity data, Journal of Computational Physics 335 (2017) 736 – 746.
- [13] M. Raissi, G. E. Karniadakis, Machine learning of linear differential equations using Gaussian processes, arXiv preprint arXiv:1701.02440 (2017).
- [14] C. E. Rasmussen, Gaussian processes for machine learning, MIT Press, 2006.
- [15] K. P. Murphy, Machine learning: a probabilistic perspective, MIT press, 2012.
- [16] V. Vapnik, The nature of statistical learning theory, Springer Science & Business Media, 2013.
- [17] B. Schölkopf, A. J. Smola, Learning with kernels: support vector machines, regularization, optimization, and beyond, MIT press, 2002.
- [18] M. E. Tipping, Sparse Bayesian learning and the relevance vector machine, The journal of machine learning research 1 (2001) 211–244.
- [19] A. Tikhonov, Solution of incorrectly formulated problems and the regularization method, in: Soviet Math. Dokl., volume 5, pp. 1035–1038.
- [20] A. N. Tikhonov, V. Y. Arsenin, Solutions of Ill-posed problems, W.H. Winston, 1977.
- [21] T. Poggio, F. Girosi, Networks for approximation and learning, Proceedings of the IEEE 78 (1990) 1481–1497.
- [22] R. M. Neal, Bayesian learning for neural networks, volume 118, Springer Science & Business Media, 2012.
- [23] F. Bashforth, J. C. Adams, An attempt to test the theories of capillary action: by comparing the theoretical and measured forms of drops of fluid. With an explanation of the method of integration employed in constucting the tables which give the theoretical forms of such drops, University Press, 1883.

- [24] C. Runge, Über die numerische auflösung von differentialgleichungen, Mathematische Annalen 46 (1895) 167–178.
- [25] J. C. Butcher, Numerical methods for ordinary differential equations, John Wiley & Sons, 2016.
- [26] C. E. Rasmussen, Z. Ghahramani, Occam's razor, Advances in neural information processing systems (2001) 294–300.
- [27] C. Basdevant, M. Deville, P. Haldenwang, J. Lacroix, J. Ouazzani, R. Peyret, P. Orlandi, A. Patera, Spectral and finite difference solutions of the Burgers equation, Computers & fluids 14 (1986) 23–41.
- [28] N. Aronszajn, Theory of reproducing kernels, Transactions of the American Mathematical Society 68 (1950) 337–404.
- [29] S. Saitoh, Theory of reproducing kernels and its applications, volume 189, Longman, 1988.
- [30] A. Berlinet, C. Thomas-Agnan, Reproducing kernel Hilbert spaces in probability and statistics, Springer Science & Business Media, 2011.
- [31] R. Alexander, Diagonally implicit Runge–Kutta methods for stiff ODEs, SIAM Journal on Numerical Analysis 14 (1977) 1006–1021.
- [32] A. Iserles, A first course in the numerical analysis of differential equations, 44, Cambridge University Press, 2009.
- [33] J. Hartikainen, S. Särkkä, Kalman filtering and smoothing solutions to temporal Gaussian process regression models, in: Machine Learning for Signal Processing (MLSP), 2010 IEEE International Workshop on, IEEE, pp. 379–384.
- [34] J. Hensman, N. Fusi, N. D. Lawrence, Gaussian processes for big data, arXiv preprint arXiv:1309.6835 (2013).
- [35] H. Owhadi, C. Scovel, T. Sullivan, et al., Brittleness of Bayesian inference under finite information in a continuous world, Electronic Journal of Statistics 9 (2015) 1–79.

- [36] A. M. Stuart, A. L. Teckentrup, Posterior consistency for Gaussian process approximations of Bayesian posterior distributions, arXiv preprint arXiv:1603.02004 (2016).
- [37] M. Schober, D. K. Duvenaud, P. Hennig, Probabilistic ODE solvers with Runge-Kutta means, in: Advances in Neural Information Processing Systems, pp. 739–747.

## 5. Appendix

## 5.1. Burgers' Equation

The covariance functions for the Burgers' equation example are given by  $k_{u,u}^{n,n}=k$ ,

$$k_{u,u}^{n,n-1} = k + \Delta t \mu^{n-1}(x') \frac{d}{dx'} k - \nu \Delta t \frac{d^2}{dx'^2} k,$$
 (45)

and

$$k_{u,u}^{n-1,n-1} = k + \Delta t \mu^{n-1}(x') \frac{d}{dx'} k - \nu \Delta t \frac{d^2}{dx'^2} k,$$

$$+ \Delta t \mu^{n-1}(x) \frac{d}{dx} k + \Delta t^2 \mu^{n-1}(x) \mu^{n-1}(x') \frac{d}{dx} \frac{d}{dx'} k$$

$$- \nu \Delta t^2 \mu^{n-1}(x) \frac{d}{dx} \frac{d^2}{dx'^2} k - \nu \Delta t \frac{d^2}{dx^2} k$$

$$- \nu \Delta t^2 \mu^{n-1}(x') \frac{d^2}{dx^2} \frac{d}{dx'} k + \nu^2 \Delta t^2 \frac{d^2}{dx^2} \frac{d^2}{dx'^2} k.$$
(46)

The only non-trivial operations in the aforementioned kernel computations are the ones involving derivatives of the kernels which can be performed using any mathematical symbolic computation program like Wolfram Mathematica.

## 5.2. Wave Equation

#### 5.2.1. Prior

The covariance functions for the wave equation example are given by

$$k_{u,u}^{n,n} = k_u + \frac{1}{4}\Delta t^2 k_v, \qquad k_{u,v}^{n,n} = \frac{1}{2}\Delta t \frac{d^2}{dx'^2} k_u + \frac{1}{2}\Delta t k_v, k_{u,u}^{n,n-1} = k_u - \frac{1}{4}\Delta t^2 k_v, \qquad k_{u,v}^{n,n-1} = -\frac{1}{2}\Delta t \frac{d^2}{dx'^2} k_u + \frac{1}{2}\Delta t k_v, k_{v,v}^{n,n} = k_v + \frac{1}{4}\Delta t^2 \frac{d^2}{dx'^2} \frac{d^2}{dx'^2} k_u, \qquad k_{v,u}^{n,n-1} = -\frac{1}{2}\Delta t k_v + \frac{1}{2}\Delta t \frac{d^2}{dx^2} k_u, k_{v,v}^{n,n-1} = k_v - \frac{1}{4}\Delta t^2 \frac{d^2}{dx'^2} \frac{d^2}{dx'^2} k_u, \qquad k_{u,u}^{n-1,n-1} = k_u + \frac{1}{4}\Delta t^2 k_v, k_{u,v}^{n-1,n-1} = -\frac{1}{2}\Delta t \frac{d^2}{dx'^2} k_u - \frac{1}{2}\Delta t k_v, \qquad k_{v,v}^{n-1,n-1} = k_v + \frac{1}{4}\Delta t^2 \frac{d^2}{dx'^2} \frac{d^2}{dx'^2} k_u.$$

$$(47)$$

It is worth highlighting that the only non-trivial but straightforward operations involved in the aforementioned kernel computations are

$$\frac{d^2}{dx'^2}k_u(x,x';\theta_u) = \frac{d^2}{dx^2}k_u(x,x';\theta_u) 
= \gamma_u^2 w_u e^{-\frac{1}{2}w_u(x-x')^2} \left(w_u(x-x')^2 - 1\right), 
\frac{d^2}{dx^2}\frac{d^2}{dx'^2}k_u(x,x';\theta_u) = \gamma_u^2 w_u^2 e^{-\frac{1}{2}w_u(x-x')^2} \left(w_u(x-x')^2 \left(w_u(x-x')^2 - 6\right) + 3\right).$$

## 5.2.2. Training

The hyper-parameters  $\theta_u$  and  $\theta_v$  can be trained by minimizing the Negative Log Marginal Likelihood resulting from

$$\begin{bmatrix} \boldsymbol{u}_{b}^{n} \\ \boldsymbol{u}^{n-1} \\ \boldsymbol{v}^{n-1} \end{bmatrix} \sim \mathcal{N}(0, \boldsymbol{K}), \tag{49}$$

where  $\{\boldsymbol{x}_b^n, \boldsymbol{u}_b^n\}$  are the data on the boundary,  $\{\boldsymbol{x}_u^{n-1}, \boldsymbol{u}^{n-1}\}$ ,  $\{\boldsymbol{x}_v^{n-1}, \boldsymbol{v}^{n-1}\}$  are artificially generated data, and

$$\bm{K} := \left[\begin{array}{cccc} \bm{K}_{u,u}^{n,n} + \sigma_n^2 I & \bm{K}_{u,u}^{n,n-1} & \bm{K}_{u,v}^{n,n-1} \ \bm{K}_{u,u}^{n-1,n-1} + \sigma_{u,n-1}^2 I & \bm{K}_{u,v}^{n-1,n-1} \ \bm{K}_{v,v}^{n-1,n-1} + \sigma_{v,n-1}^2 I \end{array}\right],$$

where

$$\begin{array}{ll} \pmb{K}_{u,u}^{n,n} = k_{u,u}^{n,n}(\pmb{x}_b^n, \pmb{x}_b^n), & \pmb{K}_{u,u}^{n,n-1} = k_{u,u}^{n,n-1}(\pmb{x}_b^n, \pmb{x}_u^{n-1}), \\ \pmb{K}_{u,v}^{n,n-1} = k_{u,v}^{n,n-1}(\pmb{x}_b^n, \pmb{x}_v^{n-1}), & \pmb{K}_{u,u}^{n-1,n-1} = k_{u,u}^{n-1,n-1}(\pmb{x}_u^{n-1}, \pmb{x}_u^{n-1}), \\ \pmb{K}_{u,v}^{n-1,n-1} = k_{u,v}^{n-1,n-1}(\pmb{x}_u^{n-1}, \pmb{x}_u^{n-1}), & \pmb{K}_{v,v}^{n-1,n-1} = k_{v,v}^{n-1,n-1}(\pmb{x}_v^{n-1}, \pmb{x}_v^{n-1}). \end{array}$$

Here, the data on the boundary are given by

$$\boldsymbol{x}_b^n = \left[ \begin{array}{c} 0 \ 1 \end{array} \right], \quad \boldsymbol{u}_b^n = \left[ \begin{array}{c} 0 \ 0 \end{array} \right],$$

which correspond to the Dirichlet boundary conditions (22).

#### 5.2.3. Posterior

In order to predict  $u^n(x_{*u}^n)$  and  $v^n(x_{*v}^n)$  at new test points  $x_{*u}^n$  and  $x_{*v}^n$ , respectively, we use the following conditional distribution

$$\begin{aligned} & \left[\begin{array}{c} \boldsymbol{u}^n(x_{*u}^n) \ \boldsymbol{v}^n(x_{*v}^n) \end{array}\right] & \left[\begin{array}{c} \boldsymbol{u}_b^n \ \boldsymbol{v}^{n-1} \end{array}\right] \sim \ & \mathcal{N}\left(\boldsymbol{q}^T\boldsymbol{K}^{-1} \left[\begin{array}{c} \boldsymbol{u}_b^n \ \boldsymbol{u}^{n-1} \ \boldsymbol{v}^{n-1} \end{array}\right], \left[\begin{array}{c} k_{u,u}^{n,n}(x_{*u}^n, x_{*u}^n) & k_{u,v}^{n,n}(x_{*u}^n, x_{*v}^n) \ k_{v,v}^{n,n}(x_{*v}^n, x_{*v}^n) \end{array}\right] - \boldsymbol{q}^T\boldsymbol{K}^{-1}\boldsymbol{q} \end{array}\right), \end{aligned}$$

where  $\boldsymbol{q} = [\boldsymbol{q}_u \ \boldsymbol{q}_v]$  and

$$\begin{array}{lll} \boldsymbol{q}_u^T & := & \left[ \begin{array}{cccc} k_{u,u}^{n,n}(x_{*u}^n,\boldsymbol{x}_b^n) & k_{u,u}^{n,n-1}(x_{*u}^n,\boldsymbol{x}_u^{n-1}) & k_{u,v}^{n,n-1}(x_{*u}^n,\boldsymbol{x}_v^{n-1}) \end{array} \right], \\ \boldsymbol{q}_v^T & := & \left[ \begin{array}{cccc} k_{v,u}^{n,n}(x_{*v}^n,\boldsymbol{x}_b^n) & k_{v,u}^{n,n-1}(x_{*v}^n,\boldsymbol{x}_u^{n-1}) & k_{v,v}^{n,n-1}(x_{*v}^n,\boldsymbol{x}_v^{n-1}) \end{array} \right]. \end{array}$$

## 5.2.4. Propagating Uncertainty

Since  $\{\boldsymbol{x}_u^{n-1}, \boldsymbol{u}^{n-1}\}$  and  $\{\boldsymbol{x}_v^{n-1}, \boldsymbol{v}^{n-1}\}$  are artificially generated data, to properly propagate the uncertainty associated with the initial data, we have to marginalize them out by employing

$$\left[\begin{array}{c} \boldsymbol{u}^{n-1} \ \boldsymbol{v}^{n-1} \end{array}\right] \sim \mathcal{N}\left(\left[\begin{array}{c} \boldsymbol{\mu}_u^{n-1} \ \boldsymbol{\mu}_v^{n-1} \end{array}\right], \left[\begin{array}{c} \Sigma_{u,u}^{n-1,n-1} & \Sigma_{u,v}^{n-1,n-1} \ \Sigma_{v,v}^{n-1,n-1} \end{array}\right]\right),$$

to obtain

$$\begin{bmatrix}\nu^{n}(x_{*u}^{n}) \\
v^{n}(x_{*v}^{n})
\end{bmatrix} \mid \mathbf{u}_{b}^{n} \sim$$

$$\mathcal{N} \left( \begin{bmatrix} \mu_{u}^{n}(x_{*u}^{n}) \\ \mu_{v}^{n}(x_{*v}^{n}) \end{bmatrix}, \begin{bmatrix} \Sigma_{u,u}^{n,n}(x_{*u}^{n}, x_{*u}^{n}) & \Sigma_{u,v}^{n,n}(x_{*u}^{n}, x_{*v}^{n}) \\ \Sigma_{v,v}^{n,n}(x_{*v}^{n}, x_{*v}^{n}) \end{bmatrix} \right),$$
(50)

where

$$\begin{bmatrix} \mu_u^n(x_{*u}^n) \\ \mu_v^n(x_{*v}^n) \end{bmatrix} = \boldsymbol{q}^T \boldsymbol{K}^{-1} \begin{bmatrix} \boldsymbol{u}_b^n \\ \boldsymbol{\mu}_u^{n-1} \\ \boldsymbol{\mu}_v^{n-1} \end{bmatrix},$$

and

$$\begin{aligned} & \left[ \begin{array}{cccc} \Sigma_{u,u}^{n,n}(x_{*u}^{n},x_{*u}^{n}) & \Sigma_{u,v}^{n,n}(x_{*u}^{n},x_{*v}^{n}) \ \Sigma_{v,v}^{n,n}(x_{*v}^{n},x_{*v}^{n}) \end{array} \right] = \left[ \begin{array}{cccc} k_{u,u}^{n,n}(x_{*u}^{n},x_{*v}^{n}) & k_{u,v}^{n,n}(x_{*u}^{n},x_{*v}^{n}) \ k_{v,v}^{n,n}(x_{*v}^{n},x_{*v}^{n}) \end{array} \right] - \ & \begin{array}{cccc} \boldsymbol{q}^{T}\boldsymbol{K}^{-1}\boldsymbol{q} + \boldsymbol{q}^{T}\boldsymbol{K}^{-1}\boldsymbol{q} & \Sigma_{u,u}^{n-1,n-1} \ \Sigma_{v,v}^{n-1,n-1} \end{array} \right] \boldsymbol{K}^{-1}\boldsymbol{q}. \end{aligned}$$

Now, we can use the resulting posterior distribution to obtain the artificially generated data  $\{x_u^n, u^n\}$  and  $\{x_v^n, v^n\}$  for the next time step with

$$\begin{bmatrix} \mathbf{u}^{n} \\ \mathbf{v}^{n} \end{bmatrix} \sim \mathcal{N} \left( \begin{bmatrix} \boldsymbol{\mu}_{u}^{n} \\ \boldsymbol{\mu}_{v}^{n} \end{bmatrix}, \begin{bmatrix} \boldsymbol{\Sigma}_{u,u}^{n,n} & \boldsymbol{\Sigma}_{u,v}^{n,n} \\ \boldsymbol{\Sigma}_{v,v}^{n,n} \end{bmatrix} \right). \tag{51}$$

#### 5.3. Advection Equation

#### 5.3.1. Prior

The covariance functions for the advection equation example are given by

$$\begin{array}{ll} k_{u,3}^{n+1,n} = k_{u,u}^{n+1,n+1}, & k_{u,3}^{n+\tau_2,n} = b_2 \Delta t \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2}, \\ k_{u,2}^{n+\tau_2,n} = k_{u,u}^{n+\tau_2,n+\tau_2} + a_{22} \Delta t \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2}, & k_{u,1}^{n+\tau_2,n} = a_{12} \Delta t \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2}, \\ k_{u,3}^{n+\tau_1,n} = b_1 \Delta t \frac{d}{dx'} k_{u,u}^{n+\tau_1,n+\tau_1}, & k_{u,2}^{n+\tau_1,n} = a_{21} \Delta t \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2}, \\ k_{u,1}^{n+\tau_1,n} = k_{u,u}^{n+\tau_1,n+\tau_1} + a_{11} \Delta t \frac{d}{dx'} k_{u,u}^{n+\tau_1,n+\tau_1}, & k_{u,2}^{n+\tau_1,n+\tau_1} = a_{21} \Delta t \frac{d}{dx'} k_{u,u}^{n+\tau_1,n+\tau_1}, \end{array}$$

and

$$k_{3,3}^{n,n} = k_{u,u}^{n+1,n+1} + b_1^2 \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_1,n+\tau_1} + b_2^2 \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2}$$

$$k_{3,2}^{n,n} = b_2 \Delta t \frac{d}{dx} k_{u,u}^{n+\tau_2,n+\tau_2} + a_{21} b_1 \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_1,n+\tau_1}$$

$$+ a_{22} b_2 \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2} ,$$

$$k_{3,1}^{n,n} = b_1 \Delta t \frac{d}{dx} k_{u,u}^{n+\tau_1,n+\tau_1} + a_{11} b_1 \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_1,n+\tau_1}$$

$$+ a_{12} b_2 \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2} ,$$

$$\begin{array}{lcl} k_{2,2}^{n,n} & = & k_{u,u}^{n+\tau_2,n+\tau_2} + a_{21}^2 \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_1,n+\tau_1} + a_{22}^2 \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2}, \\ k_{2,1}^{n,n} & = & a_{12} \Delta t \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2} + a_{21} \Delta t \frac{d}{dx} k_{u,u}^{n+\tau_1,n+\tau_1} \\ & + & a_{21} a_{11} \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_1,n+\tau_1} + a_{22} a_{12} \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2}, \end{array}$$

$$k_{1,1}^{n,n} = k_{u,u}^{n+\tau_1,n+\tau_1} + a_{11}^2 \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_1,n+\tau_1} + a_{12}^2 \Delta t^2 \frac{d}{dx} \frac{d}{dx'} k_{u,u}^{n+\tau_2,n+\tau_2}.$$

## 5.3.2. Training

The matrix K used in the distribution (37) is given by

$$\boldsymbol{K} = \begin{bmatrix} K_{b,b}^{n+1,n+1} & 0 & 0 & \boldsymbol{K}_{b,3}^{n+1,n} & 0 & 0 \\ K_{b,b}^{n+\tau_2,n+\tau_2} & 0 & \boldsymbol{K}_{b,3}^{n+\tau_2,n} & \boldsymbol{K}_{b,2}^{n+\tau_2,n} & \boldsymbol{K}_{b,1}^{n+\tau_2,n} \\ K_{b,b}^{n+\tau_1,n+\tau_1} & \boldsymbol{K}_{b,3}^{n+\tau_1,n} & \boldsymbol{K}_{b,2}^{n+\tau_1,n} & \boldsymbol{K}_{b,1}^{n+\tau_1,n} \\ K_{3,3}^{n,n} + \sigma_n^2 I & \boldsymbol{K}_{3,2}^{n,n} & \boldsymbol{K}_{3,1}^{n,n} \\ K_{2,2}^{n,n} + \sigma_n^2 I & \boldsymbol{K}_{1,1}^{n,n} + \sigma_n^2 I \end{bmatrix},$$

where

$$\begin{split} K_{b,b}^{n+1,n+1} &= k_{u,u}^{n+1,n+1}(1,1) - k_{u,u}^{n+1,n+1}(1,0) \\ &- k_{u,u}^{n+1,n+1}(0,1) + k_{u,u}^{n+1,n+1}(0,0), \\ K_{b,b}^{n+\tau_2,n+\tau_2} &= k_{u,u}^{n+\tau_2,n+\tau_2}(1,1) - k_{u,u}^{n+\tau_2,n+\tau_2}(1,0) \\ &- k_{u,u}^{n+\tau_2,n+\tau_2}(0,1) + k_{u,u}^{n+\tau_2,n+\tau_2}(0,0), \\ K_{b,b}^{n+\tau_1,n+\tau_1} &= k_{u,u}^{n+\tau_1,n+\tau_1}(1,1) - k_{u,u}^{n+\tau_1,n+\tau_1}(1,0) \\ &- k_{u,u}^{n+\tau_1,n+\tau_1}(0,1) + k_{u,u}^{n+\tau_1,n+\tau_1}(0,0), \end{split}$$

$$\begin{array}{lcl} \boldsymbol{K}_{b,i}^{n+1,n} & = & k_{u,i}^{n+1,n}(1,\boldsymbol{x}^n) - k_{u,i}^{n+1,n}(0,\boldsymbol{x}^n), \ i = 3,2,1, \\ \boldsymbol{K}_{b,i}^{n+\tau_2,n} & = & k_{u,i}^{n+\tau_2,n}(1,\boldsymbol{x}^n) - k_{u,i}^{n+\tau_2,n}(0,\boldsymbol{x}^n), \ i = 3,2,1, \\ \boldsymbol{K}_{b,i}^{n+\tau_1,n} & = & k_{u,i}^{n+\tau_1,n}(1,\boldsymbol{x}^n) - k_{u,i}^{n+\tau_1,n}(0,\boldsymbol{x}^n), \ i = 3,2,1, \\ \boldsymbol{K}_{i,j}^{n,n} & = & k_{i,j}^{n,n}(\boldsymbol{x}^n,\boldsymbol{x}^n), \quad i,j = 3,2,1, \ j \leq i. \end{array}$$

#### 5.3.3. Posterior

In order to predict  $u^{n+1}(x_*^{n+1})$  at a new test point  $x_*^{n+1}$ , we use

$$\begin{align*} u^{n+1}(x_*^{n+1}) & \left[\begin{array}{c} u^{n+1}(1) - u^{n+1}(0) &= 0 \ u^{n+\tau_2}(1) - u^{n+\tau_2}(0) &= 0 \ u^{n+\tau_1}(1) - u^{n+\tau_1}(0) &= 0 \ u^n \end{array}\right] \sim \ \mathcal{N} \left(\boldsymbol{q}^T \boldsymbol{K}^{-1} & \left[\begin{array}{c} 0 \ 0 \ 0 \ u^n \ u^n \end{array}\right], k_{u,u}^{n+1,n+1}(x_*^{n+1},x_*^{n+1}) - \boldsymbol{q}^T \boldsymbol{K}^{-1} \boldsymbol{q} \end{array}\right], \end{array}$$

where

$$\boldsymbol{q} := \left[ \begin{array}{c} k_{u,u}^{n+1,n+1}(1,x_*^{n+1}) - k_{u,u}^{n+1,n+1}(0,x_*^{n+1}) \\ 0 \\ 0 \\ k_{3,u}^{n,n+1}(\boldsymbol{x}^n,x_*^{n+1}) \\ k_{2,u}^{n,n+1}(\boldsymbol{x}^n,x_*^{n+1}) \\ k_{1,u}^{n,n+1}(\boldsymbol{x}^n,x_*^{n+1}) \end{array} \right].$$

#### 5.3.4. Propagating Uncertainty

To propagate the uncertainty associate with the noisy initial data through time we have to marginalize out the artificially generated data  $\{x^n, u^n\}$  by employing

$$\boldsymbol{u}^n \sim \mathcal{N}\left(\boldsymbol{\mu}^n, \boldsymbol{\Sigma}^{n,n}\right),$$

to obtain

$$u^{n+1}(x_*^{n+1}) \mid \begin{bmatrix} u^{n+1}(1) - u^{n+1}(0) = 0 \\ u^{n+\tau_2}(1) - u^{n+\tau_2}(0) = 0 \\ u^{n+\tau_1}(1) - u^{n+\tau_1}(0) = 0 \end{bmatrix}$$

$$\sim \mathcal{N}\left(\mu^{n+1}(x_*^{n+1}), \Sigma^{n+1,n+1}(x_*^{n+1}, x_*^{n+1})\right),$$
(52)

where

$$\mu^{n+1}(x_*^{n+1}) = \boldsymbol{q}^T \boldsymbol{K}^{-1} \left[\begin{array}{c} 0 \ 0 \ 0 \ \boldsymbol{\mu}^n \ \boldsymbol{\mu}^n \ \boldsymbol{\mu}^n \end{array}\right],$$

and

Now, we can use the resulting posterior distribution (52) to obtain the artificially generated data  $\{x^{n+1}, u^{n+1}\}$  with

$$\boldsymbol{u}^{n+1} \sim \mathcal{N}\left(\boldsymbol{\mu}^{n+1}, \boldsymbol{\Sigma}^{n+1, n+1}\right).$$
 (53)

## 5.4. Heat equation

## 5.4.1. Prior

The covariance functions for the Heat equation are given by

$$k_{u,v}^{n+1,n+1} = \frac{d}{dx'_2} k_{u,u}^{n+1,n+1}, \qquad (54)$$

$$k_{u,3}^{n+1,n} = k_{u,u}^{n+1,n+1} - \frac{1}{2} \Delta t \frac{d^2}{dx'_1^2} k_{u,u}^{n+1,n+1} - \frac{1}{2} \Delta t \frac{d^2}{dx'_2^2} k_{u,u}^{n+1,n+1},$$

$$k_{v,v}^{n+1,n+1} = \frac{d}{dx_2} \frac{d}{dx'_2} k_{u,u}^{n+1,n+1},$$

$$k_{v,3}^{n+1,n} = \frac{d}{dx_2} k_{u,u}^{n+1,n+1} - \frac{1}{2} \Delta t \frac{d}{dx_2} \frac{d^2}{dx'_1^2} k_{u,u}^{n+1,n+1} - \frac{1}{2} \Delta t \frac{d}{dx_2} \frac{d^2}{dx'_2^2} k_{u,u}^{n+1,n+1},$$

$$k_{u,v}^{n,n} = \frac{d}{dx'_2} k_{u,u}^{n,n},$$

$$k_{u,v}^{n,n} = -\frac{1}{2} \Delta t \frac{d^2}{dx'_1^2} k_{u,u}^{n,n} - \frac{1}{2} \Delta t \frac{d^2}{dx'_2^2} k_{u,u}^{n,n},$$

$$k_{u,1}^{n,n} = k_{u,u}^{n,n},$$

$$k_{v,v}^{n,n} = \frac{d}{dx_2} \frac{d}{dx'_2} k_{u,u}^{n,n},$$

$$k_{v,v}^{n,n} = -\frac{1}{2} \Delta t \frac{d}{dx_2} \frac{d^2}{dx'_1^2} k_{u,u}^{n,n} - \frac{1}{2} \Delta t \frac{d}{dx_2} \frac{d^2}{dx'_2^2} k_{u,u}^{n,n},$$

$$k_{v,1}^{n,n} = \frac{d}{dx_2} k_{u,u}^{n,n},$$

$$k_{v,1}^{n,n} = \frac{d}{dx_2} k_{u,u}^{n,n},$$

and

$$k_{3,3}^{n,n} = k_{u,u}^{n+1,n+1} - \frac{1}{2}\Delta t \frac{d^2}{dx_1'^2} k_{u,u}^{n+1,n+1} - \frac{1}{2}\Delta t \frac{d^2}{dx_2'^2} k_{u,u}^{n+1,n+1}$$

$$+ \frac{1}{4}\Delta t^2 \frac{d^2}{dx_1^2} \frac{d^2}{dx_1'^2} k_{u,u}^{n,n} + \frac{1}{4}\Delta t^2 \frac{d^2}{dx_1^2} \frac{d^2}{dx_2'^2} k_{u,u}^{n,n}$$

$$- \frac{1}{2}\Delta t \frac{d^2}{dx_1^2} k_{u,u}^{n+1,n+1} + \frac{1}{4}\Delta t^2 \frac{d^2}{dx_1^2} \frac{d^2}{dx_1'^2} k_{u,u}^{n+1,n+1} + \frac{1}{4}\Delta t^2 \frac{d^2}{dx_2^2} \frac{d^2}{dx_2'^2} k_{u,u}^{n+1,n+1}$$

$$+ \frac{1}{4}\Delta t^2 \frac{d^2}{dx_2^2} \frac{d^2}{dx_1'^2} k_{u,u}^{n,n} + \frac{1}{4}\Delta t^2 \frac{d^2}{dx_2^2} \frac{d^2}{dx_2'^2} k_{u,u}^{n,n}$$

$$- \frac{1}{2}\Delta t \frac{d^2}{dx_2^2} k_{u,u}^{n+1,n+1} + \frac{1}{4}\Delta t^2 \frac{d^2}{dx_2^2} \frac{d^2}{dx_1'^2} k_{u,u}^{n+1,n+1} + \frac{1}{4}\Delta t^2 \frac{d^2}{dx_2^2} \frac{d^2}{dx_1'^2} k_{u,u}^{n+1,n+1}$$

$$k_{3,1}^{n,n} = -\frac{1}{2}\Delta t \frac{d^2}{dx_1^2} k_{u,u}^{n,n} - \frac{1}{2}\Delta t \frac{d^2}{dx_2^2} k_{u,u}^{n,n},$$
  
$$k_{1,1}^{n,n} = k_{u,u}^{n,n}.$$

## 5.4.2. Training

The matrix K used in the distribution (44) is given by

The matrix 
$$\boldsymbol{K}$$
 used in the distribution (44) is given by 
$$\boldsymbol{K} = \begin{bmatrix} \boldsymbol{K}_{D,D}^{n+1,n+1} & \boldsymbol{K}_{D,N}^{n+1,n+1} & 0 & 0 & \boldsymbol{K}_{D,3}^{n+1,n} & 0 \\ \boldsymbol{K}_{D,D}^{n+1,n+1} & 0 & 0 & \boldsymbol{K}_{N,3}^{n+1,n} & 0 \\ \boldsymbol{K}_{D,D}^{n,n} & \boldsymbol{K}_{D,N}^{n,n} & \boldsymbol{K}_{D,3}^{n,n} & \boldsymbol{K}_{D,1}^{n,n} \\ \boldsymbol{K}_{N,N}^{n,n} & \boldsymbol{K}_{N,3}^{n,n} & \boldsymbol{K}_{N,1}^{n,n} \\ \boldsymbol{K}_{3,3}^{n,n} & \boldsymbol{K}_{3,1}^{n,n} \\ \boldsymbol{K}_{1,1}^{n,n} \end{bmatrix}.$$

Here,

$$\mathbf{K}_{D,D}^{n+1,n+1} = k_{u,u}^{n+1,n+1} \left( (\mathbf{x}_{1,D}^{n+1}, \mathbf{x}_{2,D}^{n+1}), (\mathbf{x}_{1,D}^{n+1}, \mathbf{x}_{2,D}^{n+1}) \right) + \sigma_{D,n+1}^{2} I, \quad (56)$$

$$\mathbf{K}_{D,N}^{n+1,n+1} = k_{u,v}^{n+1,n+1} \left( (\mathbf{x}_{1,D}^{n+1}, \mathbf{x}_{2,D}^{n+1}), (\mathbf{x}_{1,N}^{n+1}, \mathbf{x}_{2,N}^{n+1}) \right), \\
\mathbf{K}_{D,3}^{n+1,n} = k_{u,3}^{n+1,n} \left( (\mathbf{x}_{1,D}^{n+1}, \mathbf{x}_{2,D}^{n+1}), (\mathbf{x}_{1}^{n}, \mathbf{x}_{2}^{n}) \right), \\
\mathbf{K}_{N,N}^{n+1,n+1} = k_{v,v}^{n+1,n+1} \left( (\mathbf{x}_{1,N}^{n+1}, \mathbf{x}_{2,N}^{n+1}), (\mathbf{x}_{1,N}^{n+1}, \mathbf{x}_{2,N}^{n+1}) \right) + \sigma_{N,n+1}^{2} I, \\
\mathbf{K}_{N,3}^{n+1,n} = k_{v,3}^{n+1,n} \left( (\mathbf{x}_{1,N}^{n+1}, \mathbf{x}_{2,N}^{n+1}), (\mathbf{x}_{1}^{n}, \mathbf{x}_{2}^{n}) \right),$$

$$\begin{array}{lll} \boldsymbol{K}_{D,D}^{n,n} & = & k_{u,u}^{n,n} \left( (\boldsymbol{x}_{1,D}^{n}, \boldsymbol{x}_{2,D}^{n}), (\boldsymbol{x}_{1,D}^{n}, \boldsymbol{x}_{2,D}^{n}) \right) + \sigma_{D,n}^{2} I, \\ \boldsymbol{K}_{D,N}^{n,n} & = & k_{u,v}^{n,n} \left( (\boldsymbol{x}_{1,D}^{n}, \boldsymbol{x}_{2,D}^{n}), (\boldsymbol{x}_{1,N}^{n}, \boldsymbol{x}_{2,N}^{n}) \right), \\ \boldsymbol{K}_{D,3}^{n,n} & = & k_{u,x}^{n,n} \left( (\boldsymbol{x}_{1,D}^{n}, \boldsymbol{x}_{2,D}^{n}), (\boldsymbol{x}_{1}^{n}, \boldsymbol{x}_{2}^{n}) \right), \\ \boldsymbol{K}_{D,1}^{n,n} & = & k_{u,1}^{n,n} \left( (\boldsymbol{x}_{1,D}^{n}, \boldsymbol{x}_{2,D}^{n}), (\boldsymbol{x}_{1}^{n}, \boldsymbol{x}_{2}^{n}) \right), \\ \boldsymbol{K}_{N,N}^{n,n} & = & k_{v,v}^{n,n} \left( (\boldsymbol{x}_{1,N}^{n}, \boldsymbol{x}_{2,N}^{n}), (\boldsymbol{x}_{1,N}^{n}, \boldsymbol{x}_{2,N}^{n}) \right) + \sigma_{N,n}^{2} I, \\ \boldsymbol{K}_{N,3}^{n,n} & = & k_{v,3}^{n,n} \left( (\boldsymbol{x}_{1,N}^{n}, \boldsymbol{x}_{2,N}^{n}), (\boldsymbol{x}_{1}^{n}, \boldsymbol{x}_{2}^{n}) \right), \\ \boldsymbol{K}_{N,1}^{n,n} & = & k_{v,1}^{n,n} \left( (\boldsymbol{x}_{1,N}^{n}, \boldsymbol{x}_{2,N}^{n}), (\boldsymbol{x}_{1}^{n}, \boldsymbol{x}_{2}^{n}) \right), \end{array}$$

$$\begin{array}{lcl} \boldsymbol{K}_{3,3}^{n,n} & = & k_{3,3}^{n,n} \left( (\boldsymbol{x}_1^n, \boldsymbol{x}_2^n), (\boldsymbol{x}_1^n, \boldsymbol{x}_2^n) \right) + \sigma_n^2 I, \\ \boldsymbol{K}_{3,1}^{n,n} & = & k_{3,1}^{n,n} \left( (\boldsymbol{x}_1^n, \boldsymbol{x}_2^n), (\boldsymbol{x}_1^n, \boldsymbol{x}_2^n) \right), \\ \boldsymbol{K}_{1,1}^{n,n} & = & k_{1,1}^{n,n} \left( (\boldsymbol{x}_1^n, \boldsymbol{x}_2^n), (\boldsymbol{x}_1^n, \boldsymbol{x}_2^n) \right) + \sigma_n^2 I. \end{array}$$

# 5.4.3. Posterior

In order to predict  $u^{n+1}(x_{1,*}^{n+1}, x_{2,*}^{n+1})$  at a new test point  $(x_{1,*}^{n+1}, x_{2,*}^{n+1})$ , we use

$$u^{n+1}(x_{1,*}^{n+1},x_{2,*}^{n+1}) \mid \begin{bmatrix} \boldsymbol{u}_D^{n+1} \ \boldsymbol{v}_N^{n+1} \ \boldsymbol{u}_D^n \ \boldsymbol{v}_N^n \ \boldsymbol{u}^n \end{bmatrix} \sim \left\{ \boldsymbol{u}^T \boldsymbol{K}^{-1} \begin{bmatrix} \boldsymbol{u}_D^{n+1} \ \boldsymbol{v}_N^{n+1} \ \boldsymbol{u}_D^n \ \boldsymbol{v}_N^n \ \boldsymbol{u}^n \ \boldsymbol{u}^n \end{bmatrix}, k_{u,u}^{n+1,n+1} \left( (x_{1,*}^{n+1}, x_{2,*}^{n+1}), (x_{1,*}^{n+1}, x_{2,*}^{n+1}) \right) - \boldsymbol{q}^T \boldsymbol{K}^{-1} \boldsymbol{q} \right\},$$

where

$$\bm{q} \coloneqq \left[\begin{array}{l} k_{u,u}^{n+1,n+1} \left( (\bm{x}_{1,D}^{n+1},\bm{x}_{2,D}^{n+1}), (x_{1,*}^{n+1},x_{2,*}^{n+1}) \right) \ k_{v,u}^{n+1,n+1} \left( (\bm{x}_{1,N}^{n+1},\bm{x}_{2,N}^{n+1}), (x_{1,*}^{n+1},x_{2,*}^{n+1}) \right) \ 0 \ k_{3,u}^{n,n+1} \left( (\bm{x}_{1}^{n},\bm{x}_{2}^{n}), (x_{1,*}^{n+1},x_{2,*}^{n+1}) \right) \ 0 \end{array}\right].$$

#### 5.4.4. Propagating Uncertainty

To propagate the uncertainty associate with the noisy initial data through time we have to marginalize out the artificially generated data  $\{(\boldsymbol{x}_1^n, \boldsymbol{x}_2^n), \boldsymbol{u}^n\}$  by employing

$$u^n \sim \mathcal{N}\left(\mu^n, \Sigma^{n,n}\right),$$

to obtain

$$u^{n+1}(x_{1,*}^{n+1}, x_{2,*}^{n+1}) \mid \begin{bmatrix} \boldsymbol{u}_{D}^{n+1} \\ \boldsymbol{v}_{N}^{n+1} \\ \boldsymbol{u}_{D}^{n} \\ \boldsymbol{v}_{N}^{n} \end{bmatrix}$$

$$\sim \mathcal{N} \left( \mu^{n+1}(x_{1,*}^{n+1}, x_{2,*}^{n+1}), \Sigma^{n+1,n+1}((x_{1,*}^{n+1}, x_{2,*}^{n+1}), (x_{1,*}^{n+1}, x_{2,*}^{n+1})) \right),$$
(57)

where

$$\mu^{n+1}(x_{1,*}^{n+1},x_{2,*}^{n+1}) = \boldsymbol{q}^T \boldsymbol{K}^{-1} \left[\begin{array}{c} \boldsymbol{u}_D^{n+1} \ \boldsymbol{v}_N^n \ \boldsymbol{u}_D^n \ \boldsymbol{\mu}^n \ \boldsymbol{\mu}^n \end{array}\right],$$

and

$$\Sigma^{n+1,n+1}(x_*^{n+1},x_*^{n+1}) = k_{u,u}^{n+1,n+1}(x_*^{n+1},x_*^{n+1}) - \mathbf{q}^T \mathbf{K}^{-1} \mathbf{q}$$
$$+ \mathbf{q}^T \mathbf{K}^{-1} \begin{bmatrix} 0 & 0 & 0 \\ & \mathbf{\Sigma}^{n,n} & \mathbf{\Sigma}^{n,n} \\ & & \mathbf{\Sigma}^{n,n} \end{bmatrix} \mathbf{K}^{-1} \mathbf{q}.$$

Now, we can use the resulting posterior distribution (57) to obtain the artificially generated data  $\{(\boldsymbol{x}_1^{n+1}, \boldsymbol{x}_2^{n+1}), \boldsymbol{u}^{n+1}\}$  with

$$\boldsymbol{u}^{n+1} \sim \mathcal{N}\left(\boldsymbol{\mu}^{n+1}, \boldsymbol{\Sigma}^{n+1, n+1}\right).$$
 (58)